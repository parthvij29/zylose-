#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/i2s_std.h"
#include "driver/gpio.h"
#include "driver/i2c.h"

#include "esp_err.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "nvs_flash.h"
#include "esp_http_client.h"
#include "esp_log.h"

#include "tensorflow/lite/c/common.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

#include "zylose_model.h"


// ============================================================
//                        PIN CONFIGURATION
// ============================================================

// ---------------- INMP441 ----------------
#define I2S_BCLK        GPIO_NUM_19
#define I2S_WS          GPIO_NUM_18
#define I2S_DATA        GPIO_NUM_21

// ---------------- OLED ----------------
#define OLED_SDA        GPIO_NUM_23
#define OLED_SCL        GPIO_NUM_22
#define OLED_ADDR       0x3C

// ---------------- LED ----------------
#define LED_PIN         GPIO_NUM_4


// ============================================================
//                    DASHBOARD / WI-FI
// ============================================================
// IMPORTANT:
// ESP32 and the Mac running Next.js must be on the SAME Wi-Fi.
// Classic ESP32 supports 2.4 GHz Wi-Fi.
// Replace these values with your actual network credentials.
#define WIFI_SSID       "Vivo x300"
#define WIFI_PASSWORD   "yash1701"

// Use the Mac's LAN IP, NOT 0.0.0.0
#define API_URL         "http://10.106.9.96:3000/api/events"
#define DEVICE_ID       "ZYLOSE-ESP32-01"

#define WIFI_MAX_RETRY  10
#define WIFI_CONNECT_TIMEOUT_MS 20000

static EventGroupHandle_t wifi_event_group = NULL;
static const int WIFI_CONNECTED_BIT = BIT0;
static const int WIFI_FAIL_BIT = BIT1;
static int wifi_retry_count = 0;
static bool wifi_ready = false;


// ============================================================
//                       AUDIO SETTINGS
// ============================================================

#define SAMPLE_RATE       16000
#define AUDIO_SAMPLES     16000

#define MFCC_FRAMES       98
#define MFCC_COEFFS       13
#define MEL_BINS          40

#define FFT_SIZE          512
#define WINDOW_SIZE       480
#define HOP_SIZE          160

#define TENSOR_ARENA_SIZE (100 * 1024)


// ============================================================
//                    MODEL QUANTIZATION
// ============================================================

#define INPUT_SCALE       0.05671931430697441f
#define INPUT_ZERO_POINT  30

#define OUTPUT_SCALE      0.00390625f
#define OUTPUT_ZERO_POINT -128


// ============================================================
//              ZYLOSE FALSE-POSITIVE PROTECTION
// ============================================================

#define ZYLOSE_MIN_CONFIDENCE  0.70f
#define ZYLOSE_MARGIN          0.15f


// ============================================================
//                         GLOBALS
// ============================================================

static i2s_chan_handle_t rx_handle = NULL;

static float *audio_buffer = NULL;

static uint8_t *tensor_arena = NULL;

static tflite::MicroInterpreter *interpreter = nullptr;

static TfLiteTensor *input_tensor = nullptr;
static TfLiteTensor *output_tensor = nullptr;

// Last inference scores
static float last_silence_score = 0.0f;
static float last_unknown_score = 0.0f;
static float last_zylose_score = 0.0f;

// CPU workload statistics for the current audio cycle.
// Normalized across the ESP32 dual-core CPU capacity.
// Measured with FreeRTOS tick timing; no esp_timer dependency.
static float last_cpu_utilization = 0.0f;
static uint32_t last_processing_ms = 0;


// Inference statistics (local + dashboard)
static uint32_t total_inferences = 0;
static uint32_t total_zylose = 0;
static uint32_t total_unknown = 0;
static uint32_t total_silence = 0;

// ============================================================
//                    WI-FI INITIALIZATION
// ============================================================

static void wifi_event_handler(
    void *arg,
    esp_event_base_t event_base,
    int32_t event_id,
    void *event_data
)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START)
    {
        esp_wifi_connect();
        printf("Connecting to Wi-Fi...\n");
    }
    else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED)
    {
        wifi_ready = false;

        wifi_event_sta_disconnected_t *event =
            (wifi_event_sta_disconnected_t *)event_data;

        printf(
            "Wi-Fi disconnected. Reason: %d\n",
            event ? event->reason : -1
        );

        if (wifi_retry_count < WIFI_MAX_RETRY)
        {
            wifi_retry_count++;
            esp_wifi_connect();

            printf(
                "Retrying Wi-Fi connection (%d/%d)...\n",
                wifi_retry_count,
                WIFI_MAX_RETRY
            );
        }
        else
        {
            xEventGroupSetBits(
                wifi_event_group,
                WIFI_FAIL_BIT
            );

            printf("Wi-Fi connection failed after %d retries.\n",
                   WIFI_MAX_RETRY);
        }
    }
    else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP)
    {
        ip_event_got_ip_t *event =
            (ip_event_got_ip_t *)event_data;

        wifi_retry_count = 0;
        wifi_ready = true;

        printf("\n========================================\n");
        printf("          WI-FI CONNECTED\n");
        printf("========================================\n");
        printf(
            "ESP32 IP      : " IPSTR "\n",
            IP2STR(&event->ip_info.ip)
        );
        printf(
            "Gateway       : " IPSTR "\n",
            IP2STR(&event->ip_info.gw)
        );
        printf(
            "Netmask       : " IPSTR "\n",
            IP2STR(&event->ip_info.netmask)
        );
        printf("Dashboard API : %s\n", API_URL);
        printf("Device ID     : %s\n", DEVICE_ID);
        printf("========================================\n\n");

        xEventGroupSetBits(
            wifi_event_group,
            WIFI_CONNECTED_BIT
        );
    }
}

static bool init_wifi()
{
    printf("\n========================================\n");
    printf("             WI-FI SETUP\n");
    printf("========================================\n");
    printf("SSID          : %s\n", WIFI_SSID);
    printf("Dashboard API : %s\n", API_URL);
    printf("Device ID     : %s\n", DEVICE_ID);

    esp_err_t ret = nvs_flash_init();

    if (
        ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND
    )
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }

    ESP_ERROR_CHECK(ret);

    wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(
        esp_netif_init()
    );

    ESP_ERROR_CHECK(
        esp_event_loop_create_default()
    );

    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();

    ESP_ERROR_CHECK(
        esp_wifi_init(&cfg)
    );

    ESP_ERROR_CHECK(
        esp_event_handler_register(
            WIFI_EVENT,
            ESP_EVENT_ANY_ID,
            &wifi_event_handler,
            NULL
        )
    );

    ESP_ERROR_CHECK(
        esp_event_handler_register(
            IP_EVENT,
            IP_EVENT_STA_GOT_IP,
            &wifi_event_handler,
            NULL
        )
    );

    wifi_config_t wifi_config = {};
    strncpy(
        (char *)wifi_config.sta.ssid,
        WIFI_SSID,
        sizeof(wifi_config.sta.ssid) - 1
    );
    strncpy(
        (char *)wifi_config.sta.password,
        WIFI_PASSWORD,
        sizeof(wifi_config.sta.password) - 1
    );

    // WPA2-compatible settings. Do not require PMF.
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    wifi_config.sta.pmf_cfg.capable = true;
    wifi_config.sta.pmf_cfg.required = false;

    ESP_ERROR_CHECK(
        esp_wifi_set_mode(WIFI_MODE_STA)
    );

    ESP_ERROR_CHECK(
        esp_wifi_set_config(
            WIFI_IF_STA,
            &wifi_config
        )
    );

    // Keep Wi-Fi active; useful for reliable HTTP requests.
    ESP_ERROR_CHECK(
        esp_wifi_set_ps(WIFI_PS_NONE)
    );

    ESP_ERROR_CHECK(
        esp_wifi_start()
    );

    EventBits_t bits = xEventGroupWaitBits(
        wifi_event_group,
        WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
        pdFALSE,
        pdFALSE,
        pdMS_TO_TICKS(WIFI_CONNECT_TIMEOUT_MS)
    );

    if (bits & WIFI_CONNECTED_BIT)
    {
        printf("Wi-Fi initialization successful.\n");
        return true;
    }

    if (bits & WIFI_FAIL_BIT)
    {
        printf("Wi-Fi initialization failed.\n");
        printf("TinyML will continue locally.\n");
        return false;
    }

    printf(
        "Wi-Fi connection timed out after %d ms.\n",
        WIFI_CONNECT_TIMEOUT_MS
    );
    printf("TinyML will continue locally.\n");

    return false;
}


// ============================================================
//                 SEND INFERENCE TO DASHBOARD
// ============================================================

static bool send_event_to_api(int result)
{
    if (!wifi_ready)
    {
        printf(
            "Dashboard upload skipped: Wi-Fi is not connected.\n"
        );
        return false;
    }

    const char *result_name = "silence";

    if (result == 2)
    {
        result_name = "zylose";
    }
    else if (result == 1)
    {
        result_name = "unknown";
    }

    char post_data[512];

    int written = snprintf(
        post_data,
        sizeof(post_data),
        "{"
        "\"device_id\":\"%s\","
        "\"result\":\"%s\","
        "\"confidence\":%.5f,"
        "\"silence_score\":%.5f,"
        "\"unknown_score\":%.5f,"
        "\"zylose_score\":%.5f,"
        "\"cpu_utilization\":%.2f,"
        "\"processing_time_ms\":%lu"
        "}",
        DEVICE_ID,
        result_name,
        (result == 2) ? last_zylose_score :
        (result == 1) ? last_unknown_score :
                        last_silence_score,
        last_silence_score,
        last_unknown_score,
        last_zylose_score,
        last_cpu_utilization,
        (unsigned long)last_processing_ms
    );

    if (written <= 0 || written >= (int)sizeof(post_data))
    {
        printf("ERROR: Could not build API payload.\n");
        return false;
    }

    printf("\n----------------------------------------\n");
    printf("UPLOADING INFERENCE TO DASHBOARD\n");
    printf("URL    : %s\n", API_URL);
    printf("Payload: %s\n", post_data);

    esp_http_client_config_t config = {};
    config.url = API_URL;
    config.method = HTTP_METHOD_POST;
    config.timeout_ms = 5000;
    config.keep_alive_enable = false;

    esp_http_client_handle_t client =
        esp_http_client_init(&config);

    if (client == NULL)
    {
        printf("ERROR: HTTP client initialization failed.\n");
        return false;
    }

    esp_http_client_set_header(
        client,
        "Content-Type",
        "application/json"
    );

    esp_http_client_set_post_field(
        client,
        post_data,
        written
    );

    esp_err_t err =
        esp_http_client_perform(client);

    if (err != ESP_OK)
    {
        printf(
            "HTTP request failed: %s\n",
            esp_err_to_name(err)
        );

        esp_http_client_cleanup(client);

        return false;
    }

    int status =
        esp_http_client_get_status_code(client);

    int content_length =
        esp_http_client_get_content_length(client);

    printf(
        "HTTP status      : %d\n",
        status
    );

    printf(
        "Response length  : %d\n",
        content_length
    );

    if (status >= 200 && status < 300)
    {
        printf(
            "SUCCESS: Inference uploaded to dashboard.\n"
        );
    }
    else
    {
        printf(
            "ERROR: Dashboard returned HTTP %d.\n",
            status
        );
    }

    printf("----------------------------------------\n");

    esp_http_client_cleanup(client);

    return status >= 200 && status < 300;
}


// Log every inference locally through the ESP32 serial monitor.
static void log_current_inference(int result)
{
    total_inferences++;

    const char *result_name = "silence";

    if (result == 2)
    {
        result_name = "zylose";
        total_zylose++;
    }
    else if (result == 1)
    {
        result_name = "unknown";
        total_unknown++;
    }
    else
    {
        total_silence++;
    }

    uint32_t elapsed_ms =
        (uint32_t)(xTaskGetTickCount() * portTICK_PERIOD_MS);

    printf("\\n----------------------------------------\\n");
    printf("LOCAL INFERENCE LOG #%lu\\n", (unsigned long)total_inferences);
    printf("Time since boot : %lu ms\\n", (unsigned long)elapsed_ms);
    printf("Result          : %s\\n", result_name);
    printf("Zylose score    : %.5f\\n", last_zylose_score);
    printf("Unknown score   : %.5f\\n", last_unknown_score);
    printf("Silence score   : %.5f\\n", last_silence_score);
    printf("CPU utilization : %.2f%%\\n", last_cpu_utilization);
    printf("Processing time : %lu ms\\n", (unsigned long)last_processing_ms);
    printf("\\nLOCAL TOTALS\\n");
    printf("Zylose          : %lu\\n", (unsigned long)total_zylose);
    printf("Unknown         : %lu\\n", (unsigned long)total_unknown);
    printf("Silence         : %lu\\n", (unsigned long)total_silence);
    printf("Total           : %lu\\n", (unsigned long)total_inferences);
    printf("----------------------------------------\\n");
}


// ============================================================
//                       MFCC TABLES
// ============================================================

static float hann_window[WINDOW_SIZE];

static float dct_table[MFCC_COEFFS][MEL_BINS];

static int mel_b1[MEL_BINS];
static int mel_b2[MEL_BINS];
static int mel_b3[MEL_BINS];

// Precomputed MFCC filter weights. This removes floating-point division
// from the 98-frame mel-filter loop.
static float dct_scaled_table[MFCC_COEFFS][MEL_BINS];

static bool mfcc_tables_ready = false;

// Precomputed FFT tables. This avoids repeated sinf/cosf calculations
// during every one of the 98 MFCC frames.
static float fft_twiddle_real[FFT_SIZE / 2];
static float fft_twiddle_imag[FFT_SIZE / 2];
static uint16_t fft_bit_reverse[FFT_SIZE];
static bool fft_tables_ready = false;


// ============================================================
//                         OLED
// ============================================================

static void oled_command(uint8_t cmd)
{
    uint8_t data[2];

    data[0] = 0x00;
    data[1] = cmd;

    i2c_master_write_to_device(
        I2C_NUM_0,
        OLED_ADDR,
        data,
        2,
        pdMS_TO_TICKS(100)
    );
}


static void oled_data(
    const uint8_t *data,
    size_t length
)
{
    uint8_t buffer[17];

    while (length > 0)
    {
        size_t chunk =
            (length > 16) ? 16 : length;

        buffer[0] = 0x40;

        memcpy(
            &buffer[1],
            data,
            chunk
        );

        i2c_master_write_to_device(
            I2C_NUM_0,
            OLED_ADDR,
            buffer,
            chunk + 1,
            pdMS_TO_TICKS(100)
        );

        data += chunk;
        length -= chunk;
    }
}


// ============================================================
//                       OLED INIT
// ============================================================

static void oled_init()
{
    vTaskDelay(
        pdMS_TO_TICKS(100)
    );

    oled_command(0xAE);

    oled_command(0xD5);
    oled_command(0x80);

    oled_command(0xA8);
    oled_command(0x3F);

    oled_command(0xD3);
    oled_command(0x00);

    oled_command(0x40);

    oled_command(0x8D);
    oled_command(0x14);

    oled_command(0x20);
    oled_command(0x00);

    oled_command(0xA1);

    oled_command(0xC8);

    oled_command(0xDA);
    oled_command(0x12);

    oled_command(0x81);
    oled_command(0x7F);

    oled_command(0xD9);
    oled_command(0xF1);

    oled_command(0xDB);
    oled_command(0x40);

    oled_command(0xA4);

    oled_command(0xA6);

    oled_command(0xAF);

    vTaskDelay(
        pdMS_TO_TICKS(50)
    );
}


// ============================================================
//                    OLED POSITION
// ============================================================

static void oled_set_position(
    uint8_t page,
    uint8_t column
)
{
    oled_command(
        0xB0 + page
    );

    oled_command(
        0x00 +
        (column & 0x0F)
    );

    oled_command(
        0x10 +
        ((column >> 4) & 0x0F)
    );
}


// ============================================================
//                      OLED CLEAR
// ============================================================

static void oled_clear()
{
    uint8_t zeros[16] = {0};

    for (
        int page = 0;
        page < 8;
        page++
    )
    {
        oled_set_position(
            page,
            0
        );

        for (
            int block = 0;
            block < 8;
            block++
        )
        {
            oled_data(
                zeros,
                16
            );
        }
    }
}


// ============================================================
//                     SIMPLE FONT
// ============================================================

static const uint8_t font[][5] =
{
    // SPACE
    {0x00,0x00,0x00,0x00,0x00},

    // A
    {0x7E,0x11,0x11,0x11,0x7E},

    // B
    {0x7F,0x49,0x49,0x49,0x36},

    // C
    {0x3E,0x41,0x41,0x41,0x22},

    // D
    {0x7F,0x41,0x41,0x22,0x1C},

    // E
    {0x7F,0x49,0x49,0x49,0x41},

    // F
    {0x7F,0x09,0x09,0x09,0x01},

    // G
    {0x3E,0x41,0x49,0x49,0x7A},

    // H
    {0x7F,0x08,0x08,0x08,0x7F},

    // I
    {0x00,0x41,0x7F,0x41,0x00},

    // J
    {0x20,0x40,0x41,0x3F,0x01},

    // K
    {0x7F,0x08,0x14,0x22,0x41},

    // L
    {0x7F,0x40,0x40,0x40,0x40},

    // M
    {0x7F,0x02,0x0C,0x02,0x7F},

    // N
    {0x7F,0x04,0x08,0x10,0x7F},

    // O
    {0x3E,0x41,0x41,0x41,0x3E},

    // P
    {0x7F,0x09,0x09,0x09,0x06},

    // Q
    {0x3E,0x41,0x51,0x21,0x5E},

    // R
    {0x7F,0x09,0x19,0x29,0x46},

    // S
    {0x46,0x49,0x49,0x49,0x31},

    // T
    {0x01,0x01,0x7F,0x01,0x01},

    // U
    {0x3F,0x40,0x40,0x40,0x3F},

    // V
    {0x1F,0x20,0x40,0x20,0x1F},

    // W
    {0x7F,0x20,0x18,0x20,0x7F},

    // X
    {0x63,0x14,0x08,0x14,0x63},

    // Y
    {0x03,0x04,0x78,0x04,0x03},

    // Z
    {0x61,0x51,0x49,0x45,0x43}
};


// ============================================================
//                      OLED CHAR
// ============================================================

static void oled_char(char c)
{
    if (c == ' ')
    {
        uint8_t blank[6] =
        {
            0,0,0,0,0,0
        };

        oled_data(
            blank,
            6
        );

        return;
    }

    if (
        c >= 'A' &&
        c <= 'Z'
    )
    {
        const uint8_t *glyph =
            font[
                c - 'A' + 1
            ];

        uint8_t data[6];

        for (
            int i = 0;
            i < 5;
            i++
        )
        {
            data[i] =
                glyph[i];
        }

        data[5] = 0;

        oled_data(
            data,
            6
        );
    }
}


// ============================================================
//                      OLED PRINT
// ============================================================

static void oled_print(
    const char *text
)
{
    while (*text)
    {
        oled_char(*text);
        text++;
    }
}


// ============================================================
//                    OLED TEXT SCREENS
// ============================================================

static void oled_welcome()
{
    oled_clear();

    oled_set_position(
        1,
        30
    );

    oled_print(
        "WELCOME"
    );

    oled_set_position(
        3,
        40
    );

    oled_print(
        "ZYLOSE"
    );
}


static void oled_speak()
{
    oled_clear();

    oled_set_position(
        2,
        40
    );

    oled_print(
        "SPEAK"
    );

    oled_set_position(
        4,
        40
    );

    oled_print(
        "ZYLOSE"
    );
}


static void oled_listen_now()
{
    oled_clear();

    oled_set_position(
        2,
        28
    );

    oled_print(
        "LISTEN"
    );

    oled_set_position(
        4,
        40
    );

    oled_print(
        "NOW"
    );
}


static void oled_listening()
{
    oled_clear();

    oled_set_position(
        2,
        25
    );

    oled_print(
        "LISTENING"
    );

    oled_set_position(
        4,
        40
    );

    oled_print(
        "ZYLOSE"
    );
}


static void oled_silence()
{
    oled_clear();

    oled_set_position(
        2,
        40
    );

    oled_print(
        "SILENCE"
    );

    oled_set_position(
        4,
        40
    );

    oled_print(
        "DETECTED"
    );
}


static void oled_unknown()
{
    oled_clear();

    oled_set_position(
        2,
        37
    );

    oled_print(
        "UNKNOWN"
    );

    oled_set_position(
        4,
        40
    );

    oled_print(
        "DETECTED"
    );
}


static void oled_activated()
{
    oled_clear();

    oled_set_position(
        1,
        40
    );

    oled_print(
        "ZYLOSE"
    );

    oled_set_position(
        3,
        25
    );

    oled_print(
        "ACTIVATED"
    );
}


// ============================================================
//                 BIG COUNTDOWN NUMBERS
// ============================================================

static void oled_big_number(
    int number
)
{
    oled_clear();

    static const uint8_t digits[3][7] =
    {
        // 1
        {
            0b00100,
            0b01100,
            0b00100,
            0b00100,
            0b00100,
            0b00100,
            0b01110
        },

        // 2
        {
            0b01110,
            0b10001,
            0b00001,
            0b00010,
            0b00100,
            0b01000,
            0b11111
        },

        // 3
        {
            0b11110,
            0b00001,
            0b00001,
            0b01110,
            0b00001,
            0b00001,
            0b11110
        }
    };

    if (
        number < 1 ||
        number > 3
    )
    {
        return;
    }

    const uint8_t *digit =
        digits[number - 1];

    const int SCALE = 6;

    const int WIDTH =
        5 * SCALE;

    const int HEIGHT =
        7 * SCALE;

    const int START_X =
        (128 - WIDTH) / 2;

    const int START_Y =
        (64 - HEIGHT) / 2;

    static uint8_t framebuffer[
        128 * 64 / 8
    ];

    memset(
        framebuffer,
        0,
        sizeof(framebuffer)
    );

    for (
        int row = 0;
        row < 7;
        row++
    )
    {
        for (
            int col = 0;
            col < 5;
            col++
        )
        {
            if (
                digit[row] &
                (1 << (4 - col))
            )
            {
                for (
                    int sy = 0;
                    sy < SCALE;
                    sy++
                )
                {
                    for (
                        int sx = 0;
                        sx < SCALE;
                        sx++
                    )
                    {
                        int x =
                            START_X +
                            col * SCALE +
                            sx;

                        int y =
                            START_Y +
                            row * SCALE +
                            sy;

                        if (
                            x >= 0 &&
                            x < 128 &&
                            y >= 0 &&
                            y < 64
                        )
                        {
                            framebuffer[
                                x +
                                (y / 8) * 128
                            ] |=
                                (1 << (y % 8));
                        }
                    }
                }
            }
        }
    }

    for (
        int page = 0;
        page < 8;
        page++
    )
    {
        oled_set_position(
            page,
            0
        );

        const uint8_t *page_data =
            &framebuffer[
                page * 128
            ];

        for (
            int x = 0;
            x < 128;
            x += 16
        )
        {
            oled_data(
                &page_data[x],
                16
            );
        }
    }
}


// ============================================================
//                      OLED INIT
// ============================================================

static void init_oled()
{
    printf(
        "Initializing OLED...\n"
    );

    i2c_config_t config = {};

    config.mode =
        I2C_MODE_MASTER;

    config.sda_io_num =
        OLED_SDA;

    config.scl_io_num =
        OLED_SCL;

    config.sda_pullup_en =
        GPIO_PULLUP_ENABLE;

    config.scl_pullup_en =
        GPIO_PULLUP_ENABLE;

    config.master.clk_speed =
        100000;

    ESP_ERROR_CHECK(
        i2c_param_config(
            I2C_NUM_0,
            &config
        )
    );

    ESP_ERROR_CHECK(
        i2c_driver_install(
            I2C_NUM_0,
            I2C_MODE_MASTER,
            0,
            0,
            0
        )
    );

    oled_init();

    oled_clear();

    printf(
        "OLED initialized\n"
    );
}


// ============================================================
//                         LED
// ============================================================

static void init_led()
{
    gpio_config_t config = {};

    config.pin_bit_mask =
        (1ULL << LED_PIN);

    config.mode =
        GPIO_MODE_OUTPUT;

    config.pull_up_en =
        GPIO_PULLUP_DISABLE;

    config.pull_down_en =
        GPIO_PULLDOWN_DISABLE;

    config.intr_type =
        GPIO_INTR_DISABLE;

    ESP_ERROR_CHECK(
        gpio_config(
            &config
        )
    );

    gpio_set_level(
        LED_PIN,
        0
    );
}


// ============================================================
//                          I2S
// ============================================================

static void init_i2s()
{
    printf(
        "\n========================================\n"
    );

    printf(
        "       INMP441 I2S INITIALIZATION\n"
    );

    printf(
        "========================================\n"
    );

    i2s_chan_config_t chan_cfg =
        I2S_CHANNEL_DEFAULT_CONFIG(
            I2S_NUM_0,
            I2S_ROLE_MASTER
        );

    ESP_ERROR_CHECK(
        i2s_new_channel(
            &chan_cfg,
            NULL,
            &rx_handle
        )
    );

    i2s_std_config_t std_cfg =
    {
        .clk_cfg =
            I2S_STD_CLK_DEFAULT_CONFIG(
                SAMPLE_RATE
            ),

        .slot_cfg =
            I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(
                I2S_DATA_BIT_WIDTH_32BIT,
                I2S_SLOT_MODE_MONO
            ),

        .gpio_cfg =
        {
            .mclk =
                I2S_GPIO_UNUSED,

            .bclk =
                I2S_BCLK,

            .ws =
                I2S_WS,

            .dout =
                I2S_GPIO_UNUSED,

            .din =
                I2S_DATA,

            .invert_flags =
            {
                .mclk_inv = false,
                .bclk_inv = false,
                .ws_inv = false
            }
        }
    };

    std_cfg.slot_cfg.slot_mask =
        I2S_STD_SLOT_LEFT;

    ESP_ERROR_CHECK(
        i2s_channel_init_std_mode(
            rx_handle,
            &std_cfg
        )
    );

    ESP_ERROR_CHECK(
        i2s_channel_enable(
            rx_handle
        )
    );

    printf(
        "I2S initialized successfully\n"
    );

    printf(
        "Sample Rate : 16000 Hz\n"
    );

    printf(
        "BCLK        : GPIO19\n"
    );

    printf(
        "WS          : GPIO18\n"
    );

    printf(
        "DATA        : GPIO21\n"
    );

    printf(
        "Channel     : LEFT\n"
    );
}


// ============================================================
//                       MEL CONVERSION
// ============================================================

static float hz_to_mel(
    float hz
)
{
    return
        2595.0f *
        log10f(
            1.0f +
            hz / 700.0f
        );
}


static float mel_to_hz(
    float mel
)
{
    return
        700.0f *
        (
            powf(
                10.0f,
                mel / 2595.0f
            )
            -
            1.0f
        );
}


// ============================================================
//                  PREPARE MFCC TABLES
// ============================================================

static void prepare_mfcc_tables()
{
    if (mfcc_tables_ready)
        return;

    printf(
        "Preparing MFCC tables...\n"
    );

    // --------------------------------------------------------
    // Hann window
    // --------------------------------------------------------

    for (
        int i = 0;
        i < WINDOW_SIZE;
        i++
    )
    {
        hann_window[i] =
            0.5f *
            (
                1.0f -
                cosf(
                    2.0f *
                    M_PI *
                    i /
                    (WINDOW_SIZE - 1)
                )
            );
    }

    // --------------------------------------------------------
    // Mel filter positions
    // --------------------------------------------------------

    float mel_min =
        hz_to_mel(
            0.0f
        );

    float mel_max =
        hz_to_mel(
            SAMPLE_RATE / 2.0f
        );

    for (
        int m = 0;
        m < MEL_BINS;
        m++
    )
    {
        float mel1 =
            mel_min +
            (
                mel_max -
                mel_min
            ) *
            (float)m /
            (MEL_BINS + 1);

        float mel2 =
            mel_min +
            (
                mel_max -
                mel_min
            ) *
            (float)(m + 1) /
            (MEL_BINS + 1);

        float mel3 =
            mel_min +
            (
                mel_max -
                mel_min
            ) *
            (float)(m + 2) /
            (MEL_BINS + 1);

        mel_b1[m] =
            (int)floorf(
                (
                    FFT_SIZE + 1
                ) *
                mel_to_hz(
                    mel1
                ) /
                SAMPLE_RATE
            );

        mel_b2[m] =
            (int)floorf(
                (
                    FFT_SIZE + 1
                ) *
                mel_to_hz(
                    mel2
                ) /
                SAMPLE_RATE
            );

        mel_b3[m] =
            (int)floorf(
                (
                    FFT_SIZE + 1
                ) *
                mel_to_hz(
                    mel3
                ) /
                SAMPLE_RATE
            );

        if (mel_b1[m] < 0)
            mel_b1[m] = 0;

        if (mel_b2[m] < 0)
            mel_b2[m] = 0;

        if (mel_b3[m] < 0)
            mel_b3[m] = 0;

        if (
            mel_b1[m] >
            FFT_SIZE / 2
        )
        {
            mel_b1[m] =
                FFT_SIZE / 2;
        }

        if (
            mel_b2[m] >
            FFT_SIZE / 2
        )
        {
            mel_b2[m] =
                FFT_SIZE / 2;
        }

        if (
            mel_b3[m] >
            FFT_SIZE / 2
        )
        {
            mel_b3[m] =
                FFT_SIZE / 2;
        }
    }

    // --------------------------------------------------------
    // DCT
    // --------------------------------------------------------

    for (
        int c = 0;
        c < MFCC_COEFFS;
        c++
    )
    {
        for (
            int k = 0;
            k < MEL_BINS;
            k++
        )
        {
            dct_table[c][k] =
                cosf(
                    M_PI *
                    c *
                    (k + 0.5f) /
                    MEL_BINS
                );

            float scale =
                (c == 0)
                ? sqrtf(1.0f / MEL_BINS)
                : sqrtf(2.0f / MEL_BINS);

            dct_scaled_table[c][k] =
                dct_table[c][k] * scale;
        }
    }

    mfcc_tables_ready =
        true;

    printf(
        "MFCC tables ready\n"
    );
}


// ============================================================
//                           FFT
// ============================================================

static void fft(
    float *real,
    float *imag,
    int n
)
{
    // This implementation uses precomputed bit-reversal and twiddle
    // factors. It produces the same radix-2 FFT mathematically while
    // avoiding thousands of runtime sinf/cosf calls.

    if (!fft_tables_ready || n != FFT_SIZE)
    {
        return;
    }

    // Bit reversal
    for (int i = 0; i < n; i++)
    {
        uint16_t j = fft_bit_reverse[i];

        if (i < j)
        {
            float temp = real[i];
            real[i] = real[j];
            real[j] = temp;

            temp = imag[i];
            imag[i] = imag[j];
            imag[j] = temp;
        }
    }

    // FFT stages
    for (int len = 2; len <= n; len <<= 1)
    {
        int half = len >> 1;
        int twiddle_step = FFT_SIZE / len;

        for (int i = 0; i < n; i += len)
        {
            for (int j = 0; j < half; j++)
            {
                int u = i + j;
                int v = u + half;

                int tw = j * twiddle_step;

                float wr = fft_twiddle_real[tw];
                float wi = fft_twiddle_imag[tw];

                float vr =
                    real[v] * wr -
                    imag[v] * wi;

                float vi =
                    real[v] * wi +
                    imag[v] * wr;

                float ur = real[u];
                float ui = imag[u];

                real[u] = ur + vr;
                imag[u] = ui + vi;

                real[v] = ur - vr;
                imag[v] = ui - vi;
            }
        }
    }
}


// ============================================================
//                       MFCC FRAME
// ============================================================

static void compute_mfcc_frame(
    const float *audio,
    int frame,
    float *output
)
{
    static float real[
        FFT_SIZE
    ];

    static float imag[
        FFT_SIZE
    ];

    static float power[
        FFT_SIZE / 2 + 1
    ];

    static float mel_energy[
        MEL_BINS
    ];

    int start =
        frame *
        HOP_SIZE -
        240;

    // --------------------------------------------------------
    // Window
    // --------------------------------------------------------

    for (
        int i = 0;
        i < WINDOW_SIZE;
        i++
    )
    {
        int index =
            start + i;

        float sample =
            0.0f;

        if (
            index >= 0 &&
            index < AUDIO_SAMPLES
        )
        {
            sample =
                audio[index];
        }

        real[i] =
            sample *
            hann_window[i];

        imag[i] =
            0.0f;
    }

    // Zero padding

    for (
        int i = WINDOW_SIZE;
        i < FFT_SIZE;
        i++
    )
    {
        real[i] =
            0.0f;

        imag[i] =
            0.0f;
    }

    // --------------------------------------------------------
    // FFT
    // --------------------------------------------------------

    fft(
        real,
        imag,
        FFT_SIZE
    );

    // --------------------------------------------------------
    // Power spectrum
    // --------------------------------------------------------

    for (
        int k = 0;
        k <= FFT_SIZE / 2;
        k++
    )
    {
        power[k] =
            (
                real[k] *
                real[k]
                +
                imag[k] *
                imag[k]
            )
            /
            FFT_SIZE;
    }

    // --------------------------------------------------------
    // Mel filter bank
    // --------------------------------------------------------

    for (
        int m = 0;
        m < MEL_BINS;
        m++
    )
    {
        int b1 =
            mel_b1[m];

        int b2 =
            mel_b2[m];

        int b3 =
            mel_b3[m];

        float energy =
            0.0f;

        // Rising edge
        for (
            int k = b1;
            k < b2;
            k++
        )
        {
            if (
                b2 != b1
            )
            {
                float weight =
                    (float)(k - b1) /
                    (float)(b2 - b1);

                energy +=
                    power[k] *
                    weight;
            }
        }

        // Falling edge
        for (
            int k = b2;
            k <= b3;
            k++
        )
        {
            if (
                b3 != b2
            )
            {
                float weight =
                    (float)(b3 - k) /
                    (float)(b3 - b2);

                energy +=
                    power[k] *
                    weight;
            }
        }

        if (
            energy < 1e-10f
        )
        {
            energy =
                1e-10f;
        }

        mel_energy[m] =
            logf(
                energy
            );
    }

    // --------------------------------------------------------
    // DCT-II
    // --------------------------------------------------------

    for (
        int c = 0;
        c < MFCC_COEFFS;
        c++
    )
    {
        float sum =
            0.0f;

        for (
            int k = 0;
            k < MEL_BINS;
            k++
        )
        {
            sum +=
                mel_energy[k] *
                dct_scaled_table[c][k];
        }

        output[c] = sum;
    }
}


// ============================================================
//                          MFCC
// ============================================================

static void compute_mfcc(
    float features[
        MFCC_FRAMES
    ][MFCC_COEFFS]
)
{
    printf(
        "Computing MFCC...\n"
    );

    for (
        int frame = 0;
        frame < MFCC_FRAMES;
        frame++
    )
    {
        compute_mfcc_frame(
            audio_buffer,
            frame,
            features[frame]
        );

        // Give the scheduler a chance to run without inserting a
        // millisecond delay after every MFCC frame.
        if ((frame & 3) == 3)
        {
            taskYIELD();
        }
    }

    printf(
        "MFCC calculation complete\n"
    );
}


// ============================================================
//                    MFCC NORMALIZATION
// ============================================================

static void normalize_mfcc(
    float features[
        MFCC_FRAMES
    ][MFCC_COEFFS]
)
{
    printf(
        "Normalizing MFCC...\n"
    );

    for (
        int c = 0;
        c < MFCC_COEFFS;
        c++
    )
    {
        float mean =
            0.0f;

        for (
            int f = 0;
            f < MFCC_FRAMES;
            f++
        )
        {
            mean +=
                features[f][c];
        }

        mean /=
            MFCC_FRAMES;

        float variance =
            0.0f;

        for (
            int f = 0;
            f < MFCC_FRAMES;
            f++
        )
        {
            float diff =
                features[f][c]
                -
                mean;

            variance +=
                diff *
                diff;
        }

        variance /=
            MFCC_FRAMES;

        float std =
            sqrtf(
                variance
            );

        if (
            std < 1e-8f
        )
        {
            std =
                1e-8f;
        }

        for (
            int f = 0;
            f < MFCC_FRAMES;
            f++
        )
        {
            features[f][c] =
                (
                    features[f][c]
                    -
                    mean
                )
                /
                std;
        }

        vTaskDelay(1);
    }

    printf(
        "MFCC normalized\n"
    );
}


// ============================================================
//                         MODEL INIT
// ============================================================

static bool init_model()
{
    printf(
        "\n========================================\n"
    );

    printf(
        "          LOADING ZYLOSE MODEL\n"
    );

    printf(
        "========================================\n"
    );

    const tflite::Model *model =
        tflite::GetModel(
            zylose_int8_tflite
        );

    if (
        model == nullptr
    )
    {
        printf(
            "ERROR: Model is NULL\n"
        );

        return false;
    }

    printf(
        "Model loaded successfully\n"
    );

    printf(
        "Model size: %u bytes\n",
        zylose_int8_tflite_len
    );

    tensor_arena =
        (uint8_t *)malloc(
            TENSOR_ARENA_SIZE
        );

    if (
        tensor_arena == nullptr
    )
    {
        printf(
            "ERROR: Tensor arena allocation failed\n"
        );

        return false;
    }

    printf(
        "Tensor arena allocated: %d bytes\n",
        TENSOR_ARENA_SIZE
    );

    static tflite::MicroMutableOpResolver<15>
        resolver;

    resolver.AddConv2D();
    resolver.AddDepthwiseConv2D();
    resolver.AddFullyConnected();
    resolver.AddMean();
    resolver.AddReshape();
    resolver.AddSoftmax();
    resolver.AddAdd();
    resolver.AddMul();
    resolver.AddLogistic();
    resolver.AddPad();
    resolver.AddQuantize();
    resolver.AddDequantize();
    resolver.AddMaxPool2D();
    resolver.AddAveragePool2D();

    interpreter =
        new tflite::MicroInterpreter(
            model,
            resolver,
            tensor_arena,
            TENSOR_ARENA_SIZE,
            nullptr,
            nullptr,
            false
        );

    if (
        interpreter == nullptr
    )
    {
        printf(
            "ERROR: Interpreter creation failed\n"
        );

        return false;
    }

    if (
        interpreter->AllocateTensors()
        !=
        kTfLiteOk
    )
    {
        printf(
            "ERROR: Tensor allocation failed\n"
        );

        return false;
    }

    input_tensor =
        interpreter->input(0);

    output_tensor =
        interpreter->output(0);

    printf(
        "Tensor allocation successful\n"
    );

    printf(
        "Input tensor type: %d\n",
        input_tensor->type
    );

    printf(
        "Input dimensions: %d x %d x %d x %d\n",
        input_tensor->dims->data[0],
        input_tensor->dims->data[1],
        input_tensor->dims->data[2],
        input_tensor->dims->data[3]
    );

    printf(
        "Input scale: %.6f\n",
        input_tensor->params.scale
    );

    printf(
        "Input zero point: %" PRId32 "\n",
        input_tensor->params.zero_point
    );

    printf(
        "Output tensor type: %d\n",
        output_tensor->type
    );

    printf(
        "Output dimensions: %d x %d\n",
        output_tensor->dims->data[0],
        output_tensor->dims->data[1]
    );

    printf(
        "Output scale: %.6f\n",
        output_tensor->params.scale
    );

    printf(
        "Output zero point: %" PRId32 "\n",
        output_tensor->params.zero_point
    );

    printf(
        "\nZYLOSE MODEL READY\n"
    );

    return true;
}


// ============================================================
//                        INFERENCE
// ============================================================

static int run_inference()
{
    static float features[
        MFCC_FRAMES
    ][MFCC_COEFFS];

    // --------------------------------------------------------
    // MFCC
    // --------------------------------------------------------

    compute_mfcc(
        features
    );

    // --------------------------------------------------------
    // Normalize
    // --------------------------------------------------------

    normalize_mfcc(
        features
    );

    // --------------------------------------------------------
    // Quantize
    // --------------------------------------------------------

    printf(
        "Quantizing model input...\n"
    );

    for (
        int f = 0;
        f < MFCC_FRAMES;
        f++
    )
    {
        for (
            int c = 0;
            c < MFCC_COEFFS;
            c++
        )
        {
            float value =
                features[f][c];

            int32_t q =
                (int32_t)roundf(
                    value /
                    INPUT_SCALE
                )
                +
                INPUT_ZERO_POINT;

            if (
                q > 127
            )
            {
                q = 127;
            }

            if (
                q < -128
            )
            {
                q = -128;
            }

            int index =
                f *
                MFCC_COEFFS
                +
                c;

            input_tensor
                ->data.int8[index] =
                (int8_t)q;
        }

        if (
            (f % 10) == 0
        )
        {
            vTaskDelay(1);
        }
    }

    printf(
        "Input quantization complete\n"
    );

    // --------------------------------------------------------
    // Inference
    // --------------------------------------------------------

    printf(
        "Running inference...\n"
    );

    uint32_t start =
        xTaskGetTickCount();

    TfLiteStatus status =
        interpreter->Invoke();

    uint32_t end =
        xTaskGetTickCount();

    printf(
        "Inference time: %lu ms\n",
        (unsigned long)(
            (
                end -
                start
            )
            *
            portTICK_PERIOD_MS
        )
    );

    if (
        status !=
        kTfLiteOk
    )
    {
        printf(
            "ERROR: Inference failed\n"
        );

        return 0;
    }

    // --------------------------------------------------------
    // Dequantize output
    // --------------------------------------------------------

    float scores[3];

    for (
        int i = 0;
        i < 3;
        i++
    )
    {
        scores[i] =
            (
                (
                    float
                )
                output_tensor
                    ->data.int8[i]
                -
                OUTPUT_ZERO_POINT
            )
            *
            OUTPUT_SCALE;
    }

    printf(
        "\n"
    );

    printf(
        "silence = %.5f\n",
        scores[0]
    );

    printf(
        "unknown = %.5f\n",
        scores[1]
    );

    printf(
        "zylose  = %.5f\n",
        scores[2]
    );

    // Save scores for local logging.

    last_silence_score =
        scores[0];

    last_unknown_score =
        scores[1];

    last_zylose_score =
        scores[2];

    // --------------------------------------------------------
    // Find highest class
    // --------------------------------------------------------

    int best =
        0;

    for (
        int i = 1;
        i < 3;
        i++
    )
    {
        if (
            scores[i] >
            scores[best]
        )
        {
            best =
                i;
        }
    }

    printf(
        "Raw best class: %d\n",
        best
    );

    // --------------------------------------------------------
    // ZYLOSE PROTECTION
    // --------------------------------------------------------

    if (
        best == 2
    )
    {
        float confidence =
            scores[2];

        float margin =
            scores[2] -
            scores[1];

        printf(
            "ZYLOSE confidence: %.5f\n",
            confidence
        );

        printf(
            "ZYLOSE/UNKNOWN margin: %.5f\n",
            margin
        );

        if (
            confidence >=
            ZYLOSE_MIN_CONFIDENCE
            &&
            margin >=
            ZYLOSE_MARGIN
        )
        {
            printf(
                "\n"
            );

            printf(
                "RESULT: ZYLOSE\n"
            );

            printf(
                "ZYLOSE CONFIRMED\n"
            );

            return 2;
        }

        printf(
            "\n"
        );

        printf(
            "ZYLOSE REJECTED - LOW CONFIDENCE\n"
        );

        printf(
            "RESULT: UNKNOWN\n"
        );

        return 1;
    }

    // --------------------------------------------------------
    // UNKNOWN
    // --------------------------------------------------------

    if (
        best == 1
    )
    {
        printf(
            "\nRESULT: UNKNOWN\n"
        );

        return 1;
    }

    // --------------------------------------------------------
    // SILENCE
    // --------------------------------------------------------

    printf(
        "\nRESULT: SILENCE\n"
    );

    return 0;
}


// ============================================================
//                     CAPTURE AUDIO
// ============================================================

static bool capture_audio()
{
    constexpr int RAW_CHUNK_SAMPLES =
        256;

    static int32_t raw_chunk[
        RAW_CHUNK_SAMPLES
    ];

    int samples_captured =
        0;

    while (
        samples_captured <
        AUDIO_SAMPLES
    )
    {
        int samples_to_read =
            AUDIO_SAMPLES -
            samples_captured;

        if (
            samples_to_read >
            RAW_CHUNK_SAMPLES
        )
        {
            samples_to_read =
                RAW_CHUNK_SAMPLES;
        }

        size_t bytes_requested =
            (size_t)samples_to_read *
            sizeof(int32_t);

        size_t bytes_read =
            0;

        esp_err_t ret =
            i2s_channel_read(
                rx_handle,
                raw_chunk,
                bytes_requested,
                &bytes_read,
                portMAX_DELAY
            );

        if (
            ret != ESP_OK
        )
        {
            printf(
                "I2S error: %s\n",
                esp_err_to_name(ret)
            );

            return false;
        }

        int samples_read =
            (int)(
                bytes_read /
                sizeof(int32_t)
            );

        if (
            samples_read <= 0
        )
        {
            printf(
                "ERROR: I2S returned 0 samples\n"
            );

            return false;
        }

        for (
            int i = 0;
            i < samples_read;
            i++
        )
        {
            audio_buffer[
                samples_captured +
                i
            ] =
                (float)(
                    (int16_t)(
                        raw_chunk[i] >>
                        16
                    )
                );
        }

        samples_captured +=
            samples_read;

        vTaskDelay(1);
    }

    printf(
        "Captured %d samples using chunked I2S capture\n",
        samples_captured
    );

    return true;
}


// ============================================================
//                     AUDIO DIAGNOSTICS
// ============================================================

static void print_audio_level()
{
    float min_v =
        audio_buffer[0];

    float max_v =
        audio_buffer[0];

    float sum_abs =
        0.0f;

    for (
        int i = 0;
        i < AUDIO_SAMPLES;
        i++
    )
    {
        float value =
            audio_buffer[i];

        if (
            value < min_v
        )
        {
            min_v =
                value;
        }

        if (
            value > max_v
        )
        {
            max_v =
                value;
        }

        sum_abs +=
            fabsf(value);
    }

    printf(
        "Audio min      : %.1f\n",
        min_v
    );

    printf(
        "Audio max      : %.1f\n",
        max_v
    );

    printf(
        "Audio mean abs : %.1f\n",
        sum_abs /
        AUDIO_SAMPLES
    );
}


// ============================================================
//                   COUNTDOWN 1 → 2 → 3
// ============================================================

static void countdown()
{
    oled_speak();

    printf(
        "\n"
    );

    printf(
        "SPEAK ZYLOSE\n"
    );

    vTaskDelay(
        pdMS_TO_TICKS(1000)
    );

    printf(
        "COUNTDOWN: 1\n"
    );

    oled_big_number(1);

    vTaskDelay(
        pdMS_TO_TICKS(1000)
    );

    printf(
        "COUNTDOWN: 2\n"
    );

    oled_big_number(2);

    vTaskDelay(
        pdMS_TO_TICKS(1000)
    );

    printf(
        "COUNTDOWN: 3\n"
    );

    oled_big_number(3);

    vTaskDelay(
        pdMS_TO_TICKS(1000)
    );

    printf(
        ">>> LISTEN NOW! <<<\n"
    );

    oled_listen_now();
}


// ============================================================
//                           MAIN
// ============================================================

extern "C"
void app_main(void)
{
    printf(
        "\n\n"
    );

    printf(
        "########################################\n"
    );

    printf(
        "#                                      #\n"
    );

    printf(
        "#       ZYLOSE TINYML KWS SYSTEM       #\n"
    );

    printf(
        "#                                      #\n"
    );

    printf(
        "########################################\n"
    );

    // ========================================================
    // ALLOCATE AUDIO BUFFER
    // ========================================================

    audio_buffer =
        (float *)malloc(
            AUDIO_SAMPLES *
            sizeof(float)
        );

    if (
        audio_buffer == nullptr
    )
    {
        printf(
            "ERROR: Audio buffer allocation failed\n"
        );

        return;
    }

    printf(
        "Audio buffer allocated: %d bytes\n",
        AUDIO_SAMPLES *
        sizeof(float)
    );

    // ========================================================
    // INITIALIZE HARDWARE
    // ========================================================

    init_i2s();

    init_oled();

    init_led();

    // ========================================================
    // INITIALIZE WI-FI / DASHBOARD CONNECTION
    // ========================================================

    init_wifi();

    // ========================================================
    // PREPARE MFCC
    // ========================================================

    prepare_mfcc_tables();

    // ========================================================
    // INITIALIZE MODEL
    // ========================================================

    if (
        !init_model()
    )
    {
        printf(
            "ERROR: Model initialization failed\n"
        );

        return;
    }

    // ========================================================
    // WELCOME
    // ========================================================

    printf(
        "\n"
    );

    printf(
        "WELCOME TO ZYLOSE\n"
    );

    oled_welcome();

    vTaskDelay(
        pdMS_TO_TICKS(2500)
    );

    // ========================================================
    // MAIN LOOP
    // ========================================================

    while (1)
    {
        // LED OFF
        gpio_set_level(
            LED_PIN,
            0
        );

        // ----------------------------------------------------
        // COUNTDOWN
        // ----------------------------------------------------

        countdown();

        // ----------------------------------------------------
        // RECORD AUDIO
        // ----------------------------------------------------

        printf(
            "\n"
        );

        printf(
            "========================================\n"
        );

        printf(
            "             LISTENING\n"
        );

        printf(
            "========================================\n"
        );

        // Start timing the complete audio capture + processing cycle.
        // This uses the FreeRTOS scheduler tick and is compatible with
        // ESP-IDF 5.5.5 without esp_timer.h.
        TickType_t cycle_start = xTaskGetTickCount();

        bool success =
            capture_audio();

        TickType_t record_end =
            xTaskGetTickCount();

        if (!success)
        {
            printf(
                "Audio capture failed!\n"
            );

            oled_listening();

            vTaskDelay(
                pdMS_TO_TICKS(500)
            );

            continue;
        }

        printf(
            "Captured 16000 samples\n"
        );

        printf(
            "Recording time: %lu ms\n",
            (unsigned long)(
                (
                    record_end -
                    cycle_start
                )
                *
                portTICK_PERIOD_MS
            )
        );

        // Start the measured processing section after microphone capture.
        // This includes audio diagnostics, MFCC, normalization,
        // quantization and TFLM inference.
        TickType_t processing_start = xTaskGetTickCount();

        // ----------------------------------------------------
        // AUDIO LEVEL
        // ----------------------------------------------------

        print_audio_level();

        // ----------------------------------------------------
        // INFERENCE
        // ----------------------------------------------------

        // Measure the complete TinyML processing section:
        // MFCC + normalization + quantization + TFLM inference.
        // Audio capture is intentionally excluded because i2s_channel_read()
        // blocks while waiting for microphone samples.
        int result =
            run_inference();

        TickType_t processing_end = xTaskGetTickCount();

        last_processing_ms =
            (uint32_t)((processing_end - processing_start) * portTICK_PERIOD_MS);

        // ----------------------------------------------------
        // CPU LOAD
        // ----------------------------------------------------
        //
        // Measure the application task's active processing time only.
        // Audio capture is I2S-blocking and therefore must not be
        // counted as CPU busy time.
        //
        // The result is normalized to the complete 1-second audio
        // window. It is intentionally NOT calculated from total
        // wall-clock time, so a blocking I2S wait cannot create
        // impossible values such as 226%.
        TickType_t cycle_end = xTaskGetTickCount();

        uint32_t full_cycle_ms =
            (uint32_t)((cycle_end - cycle_start) * portTICK_PERIOD_MS);

        if (full_cycle_ms == 0)
        {
            full_cycle_ms = 1;
        }

        // ESP32 is dual-core. Normalize the measured application
        // processing time across both CPU cores so the displayed value
        // represents the processing duty relative to the total available
        // CPU capacity of the dual-core chip.
        //
        // This is an application-load metric, not a claim that every
        // FreeRTOS task on both cores is being measured.
        last_cpu_utilization =
            ((float)last_processing_ms /
             ((float)full_cycle_ms * 2.0f)) * 100.0f;

        if (last_cpu_utilization < 0.0f)
        {
            last_cpu_utilization = 0.0f;
        }

        if (last_cpu_utilization > 100.0f)
        {
            last_cpu_utilization = 100.0f;
        }

        if (last_cpu_utilization > 10.0f)
        {
            printf("\nCPU UTILIZATION : %.2f%% [WARNING - ABOVE 10%%]\n",
                   last_cpu_utilization);
        }
        else
        {
            printf("\nCPU UTILIZATION : %.2f%% [PASS - BELOW 10%%]\n",
                   last_cpu_utilization);
        }

        printf("PROCESSING TIME  : %lu ms\n",
               (unsigned long)last_processing_ms);

        // ----------------------------------------------------
        // LOCAL LOGGING
        // ----------------------------------------------------

        // Keep the local serial log as before.
        log_current_inference(
            result
        );

        // ----------------------------------------------------
        // DASHBOARD LOGGING
        // ----------------------------------------------------

        // Upload the same inference to the Next.js API.
        // If Wi-Fi is unavailable, the TinyML system continues
        // working normally and the local log is still preserved.
        send_event_to_api(
            result
        );

        // ====================================================
        // ZYLOSE
        // ====================================================

        if (
            result == 2
        )
        {
            printf(
                "\n"
            );

            printf(
                "**************************************\n"
            );

            printf(
                "*                                    *\n"
            );

            printf(
                "*         ZYLOSE ACTIVATED           *\n"
            );

            printf(
                "*                                    *\n"
            );

            printf(
                "**************************************\n"
            );

            oled_activated();

            // LED ON

            gpio_set_level(
                LED_PIN,
                1
            );

            // Hold result

            vTaskDelay(
                pdMS_TO_TICKS(1500)
            );

            // LED OFF

            gpio_set_level(
                LED_PIN,
                0
            );
        }

        // ====================================================
        // UNKNOWN
        // ====================================================

        else if (
            result == 1
        )
        {
            printf(
                "\nUNKNOWN DETECTED\n"
            );

            oled_unknown();

            vTaskDelay(
                pdMS_TO_TICKS(1500)
            );
        }

        // ====================================================
        // SILENCE
        // ====================================================

        else
        {
            printf(
                "\nSILENCE DETECTED\n"
            );

            oled_silence();

            vTaskDelay(
                pdMS_TO_TICKS(1500)
            );
        }

        // ====================================================
        // BACK TO LISTENING
        // ====================================================

        printf(
            "\n"
        );

        printf(
            "Returning to listening...\n"
        );

        oled_listening();

        vTaskDelay(
            pdMS_TO_TICKS(20)
        );
    }
}



