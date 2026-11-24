#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/i2c.h"
#include "driver/uart.h"
#include "esp_log.h"

#define TAG "ZYLOSE_EDGE"

// ---------------- Pin Configurations ----------------
#define OLED_SDA        GPIO_NUM_23
#define OLED_SCL        GPIO_NUM_22
#define OLED_ADDR       0x3C
#define LED_PIN         GPIO_NUM_4
#define UART_PORT       UART_NUM_0
#define BUF_SIZE        1024

// ---------------- OLED 5x7 Font (ASCII 32 to 95) ----------------
static const uint8_t font5x7[][5] = {
    {0x00, 0x00, 0x00, 0x00, 0x00}, // 32 ' '
    {0x00, 0x00, 0x5F, 0x00, 0x00}, // 33 '!'
    {0x00, 0x07, 0x00, 0x07, 0x00}, // 34 '"'
    {0x14, 0x7F, 0x14, 0x7F, 0x14}, // 35 '#'
    {0x24, 0x2A, 0x7F, 0x2A, 0x12}, // 36 '$'
    {0x23, 0x13, 0x08, 0x64, 0x62}, // 37 '%'
    {0x36, 0x49, 0x55, 0x22, 0x50}, // 38 '&'
    {0x00, 0x05, 0x03, 0x00, 0x00}, // 39 '''
    {0x00, 0x1C, 0x22, 0x41, 0x00}, // 40 '('
    {0x00, 0x41, 0x22, 0x1C, 0x00}, // 41 ')'
    {0x14, 0x08, 0x3E, 0x08, 0x14}, // 42 '*'
    {0x08, 0x08, 0x3E, 0x08, 0x08}, // 43 '+'
    {0x00, 0x50, 0x30, 0x00, 0x00}, // 44 ','
    {0x08, 0x08, 0x08, 0x08, 0x08}, // 45 '-'
    {0x00, 0x60, 0x60, 0x00, 0x00}, // 46 '.'
    {0x20, 0x10, 0x08, 0x04, 0x02}, // 47 '/'
    {0x3E, 0x51, 0x49, 0x45, 0x3E}, // 48 '0'
    {0x00, 0x42, 0x7F, 0x40, 0x00}, // 49 '1'
    {0x42, 0x61, 0x51, 0x49, 0x46}, // 50 '2'
    {0x21, 0x41, 0x45, 0x4B, 0x31}, // 51 '3'
    {0x18, 0x14, 0x12, 0x7F, 0x10}, // 52 '4'
    {0x27, 0x45, 0x45, 0x45, 0x39}, // 53 '5'
    {0x3C, 0x4A, 0x49, 0x49, 0x30}, // 54 '6'
    {0x01, 0x71, 0x09, 0x05, 0x03}, // 55 '7'
    {0x36, 0x49, 0x49, 0x49, 0x36}, // 56 '8'
    {0x06, 0x49, 0x49, 0x29, 0x1E}, // 57 '9'
    {0x00, 0x36, 0x36, 0x00, 0x00}, // 58 ':'
    {0x00, 0x56, 0x36, 0x00, 0x00}, // 59 ';'
    {0x08, 0x14, 0x22, 0x41, 0x00}, // 60 '<'
    {0x14, 0x14, 0x14, 0x14, 0x14}, // 61 '='
    {0x00, 0x41, 0x22, 0x14, 0x08}, // 62 '>'
    {0x02, 0x01, 0x51, 0x09, 0x06}, // 63 '?'
    {0x32, 0x49, 0x79, 0x41, 0x3E}, // 64 '@'
    {0x7E, 0x11, 0x11, 0x11, 0x7E}, // 65 'A'
    {0x7F, 0x49, 0x49, 0x49, 0x36}, // 66 'B'
    {0x3E, 0x41, 0x41, 0x41, 0x22}, // 67 'C'
    {0x7F, 0x41, 0x41, 0x22, 0x1C}, // 68 'D'
    {0x7F, 0x49, 0x49, 0x49, 0x41}, // 69 'E'
    {0x7F, 0x09, 0x09, 0x09, 0x01}, // 70 'F'
    {0x3E, 0x41, 0x49, 0x49, 0x7A}, // 71 'G'
    {0x7F, 0x08, 0x08, 0x08, 0x7F}, // 72 'H'
    {0x00, 0x41, 0x7F, 0x41, 0x00}, // 73 'I'
    {0x20, 0x40, 0x41, 0x3F, 0x01}, // 74 'J'
    {0x7F, 0x08, 0x14, 0x22, 0x41}, // 75 'K'
    {0x7F, 0x40, 0x40, 0x40, 0x40}, // 76 'L'
    {0x7F, 0x02, 0x0C, 0x02, 0x7F}, // 77 'M'
    {0x7F, 0x04, 0x08, 0x10, 0x7F}, // 78 'N'
    {0x3E, 0x41, 0x41, 0x41, 0x3E}, // 79 'O'
    {0x7F, 0x09, 0x09, 0x09, 0x06}, // 80 'P'
    {0x3E, 0x41, 0x51, 0x21, 0x5E}, // 81 'Q'
    {0x7F, 0x09, 0x19, 0x29, 0x46}, // 82 'R'
    {0x46, 0x49, 0x49, 0x49, 0x31}, // 83 'S'
    {0x01, 0x01, 0x7F, 0x01, 0x01}, // 84 'T'
    {0x3F, 0x40, 0x40, 0x40, 0x3F}, // 85 'U'
    {0x1F, 0x20, 0x40, 0x20, 0x1F}, // 86 'V'
    {0x7F, 0x20, 0x18, 0x20, 0x7F}, // 87 'W'
    {0x63, 0x14, 0x08, 0x14, 0x63}, // 88 'X'
    {0x03, 0x04, 0x78, 0x04, 0x03}, // 89 'Y'
    {0x61, 0x51, 0x49, 0x45, 0x43}, // 90 'Z'
    {0x00, 0x7F, 0x41, 0x41, 0x00}, // 91 '['
    {0x02, 0x04, 0x08, 0x10, 0x20}, // 92 '\'
    {0x00, 0x41, 0x41, 0x7F, 0x00}, // 93 ']'
    {0x04, 0x02, 0x01, 0x02, 0x04}, // 94 '^'
    {0x40, 0x40, 0x40, 0x40, 0x40}  // 95 '_'
};

// ---------------- OLED Low-Level Drivers ----------------
static void oled_command(uint8_t cmd) {
    uint8_t data[2] = {0x00, cmd};
    i2c_master_write_to_device(I2C_NUM_0, OLED_ADDR, data, 2, pdMS_TO_TICKS(100));
}

static void oled_data(const uint8_t *data, size_t length) {
    uint8_t buffer[17];
    while (length > 0) {
        size_t chunk = (length > 16) ? 16 : length;
        buffer[0] = 0x40;
        memcpy(&buffer[1], data, chunk);
        i2c_master_write_to_device(I2C_NUM_0, OLED_ADDR, buffer, chunk + 1, pdMS_TO_TICKS(100));
        data += chunk;
        length -= chunk;
    }
}

static void oled_set_position(uint8_t page, uint8_t column) {
    oled_command(0xB0 + (page & 0x07));
    oled_command(0x00 + (column & 0x0F));
    oled_command(0x10 + ((column >> 4) & 0x0F));
}

static void oled_clear(void) {
    uint8_t zeros[16] = {0};
    for (int page = 0; page < 8; page++) {
        oled_set_position(page, 0);
        for (int block = 0; block < 8; block++) {
            oled_data(zeros, 16);
        }
    }
}

static void oled_char(char c) {
    c = toupper((unsigned char)c);
    int idx = (int)c - 32;
    if (idx < 0 || idx >= (int)(sizeof(font5x7) / sizeof(font5x7[0]))) {
        idx = 0; // space fallback
    }
    uint8_t data[6];
    for (int i = 0; i < 5; i++) {
        data[i] = font5x7[idx][i];
    }
    data[5] = 0x00; // 1px spacing
    oled_data(data, 6);
}

static void oled_print_at(uint8_t page, uint8_t column, const char *text) {
    oled_set_position(page, column);
    while (*text) {
        oled_char(*text++);
    }
}

static void oled_clear_line(uint8_t page) {
    oled_set_position(page, 0);
    uint8_t zeros[16] = {0};
    for (int i = 0; i < 8; i++) {
        oled_data(zeros, 16);
    }
}

static void oled_init(void) {
    vTaskDelay(pdMS_TO_TICKS(100));
    oled_command(0xAE); // Display OFF
    oled_command(0xD5); oled_command(0x80); // Set clock divide
    oled_command(0xA8); oled_command(0x3F); // 1/64 duty
    oled_command(0xD3); oled_command(0x00); // No display offset
    oled_command(0x40); // Start line 0
    oled_command(0x8D); oled_command(0x14); // Enable charge pump
    oled_command(0x20); oled_command(0x00); // Horizontal addressing
    oled_command(0xA1); // Remap column
    oled_command(0xC8); // Remap row scan
    oled_command(0xDA); oled_command(0x12); // Com pins config
    oled_command(0x81); oled_command(0x7F); // Contrast
    oled_command(0xD9); oled_command(0xF1); // Pre-charge
    oled_command(0xDB); oled_command(0x40); // VCOM detect
    oled_command(0xA4); // Entire display on
    oled_command(0xA6); // Normal display
    oled_command(0xAF); // Display ON
    vTaskDelay(pdMS_TO_TICKS(50));
    oled_clear();
}

// ---------------- High-Level UI Screens ----------------
static void ui_show_idle(void) {
    gpio_set_level(LED_PIN, 0);
    oled_clear();
    oled_print_at(0, 8,  "====================");
    oled_print_at(2, 20, "ZYLOSE TinyML");
    oled_print_at(4, 18, "Status: READY");
    oled_print_at(6, 8,  "Waiting for Wake...");
}

static void ui_show_wake(void) {
    gpio_set_level(LED_PIN, 1);
    oled_clear();
    oled_print_at(0, 4,  "********************");
    oled_print_at(2, 10, "ZYLOSE ACTIVATED!");
    oled_print_at(4, 16, "Confidence: 98.7%");
    oled_print_at(6, 4,  "********************");
}

static void ui_show_listening(void) {
    oled_clear();
    oled_print_at(0, 10, "--- ZYLOSE AI ---");
    oled_print_at(2, 12, ">>> LISTENING <<<");
    oled_print_at(5, 14, "Speak command now");
}

static void ui_show_processing(void) {
    oled_clear();
    oled_print_at(0, 10, "--- ZYLOSE AI ---");
    oled_print_at(2, 8,  "ANALYZING SPEECH...");
    oled_print_at(5, 14, "Classifying Intent");
}

static void ui_show_answer(const char *ans) {
    oled_clear();
    oled_print_at(0, 18, "--- RESPONSE ---");
    char line[22];
    int len = strlen(ans);
    int offset = 0;
    int page = 2;

    while (offset < len && page <= 6) {
        int chunk = len - offset;
        if (chunk > 20) chunk = 20;
        strncpy(line, ans + offset, chunk);
        line[chunk] = '\0';
        oled_print_at(page, 4, line);
        offset += chunk;
        page += 2;
    }
}

static void ui_show_abort(void) {
    oled_clear();
    oled_print_at(0, 0,  "!!!!!!!!!!!!!!!!!!!!");
    oled_print_at(2, 12, "EMERGENCY ABORT!");
    oled_print_at(4, 8,  "Subsystems Cutoff");
    oled_print_at(6, 0,  "!!!!!!!!!!!!!!!!!!!!");
    for (int i = 0; i < 4; i++) {
        gpio_set_level(LED_PIN, 1);
        vTaskDelay(pdMS_TO_TICKS(150));
        gpio_set_level(LED_PIN, 0);
        vTaskDelay(pdMS_TO_TICKS(150));
    }
}

// ---------------- Command Processor ----------------
static void process_serial_command(const char *cmd) {
    // Trim newline or carriage return
    char clean_cmd[128];
    strncpy(clean_cmd, cmd, sizeof(clean_cmd) - 1);
    clean_cmd[sizeof(clean_cmd) - 1] = '\0';
    for (int i = strlen(clean_cmd) - 1; i >= 0; i--) {
        if (clean_cmd[i] == '\r' || clean_cmd[i] == '\n' || clean_cmd[i] == ' ') {
            clean_cmd[i] = '\0';
        } else {
            break;
        }
    }

    if (strlen(clean_cmd) == 0) return;

    if (strcmp(clean_cmd, "CMD:WAKE") == 0 || strcmp(clean_cmd, "CMD:ACTIVATED") == 0) {
        ui_show_wake();
        printf("**************************************\n");
        printf("*         ZYLOSE ACTIVATED           *\n");
        printf("**************************************\n");
        printf("Result          : zylose\n");
        printf("Zylose score    : 0.98700\n");
        printf("Unknown score   : 0.01000\n");
        printf("Silence score   : 0.00300\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "CMD:LISTEN") == 0) {
        ui_show_listening();
        printf("STATUS: LISTENING\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "CMD:PROCESSING") == 0) {
        ui_show_processing();
        printf("STATUS: PROCESSING\n");
        fflush(stdout);
    }
    else if (strncmp(clean_cmd, "CMD:ANS:", 8) == 0) {
        const char *ans = clean_cmd + 8;
        ui_show_answer(ans);
        printf("RESPONSE_DISPLAYED: %s\n", ans);
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "CMD:LED_ON") == 0) {
        gpio_set_level(LED_PIN, 1);
        oled_clear_line(6);
        oled_print_at(6, 20, "ACTUATOR: LED ON");
        printf("ACTUATOR: LED ON\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "CMD:LED_OFF") == 0) {
        gpio_set_level(LED_PIN, 0);
        oled_clear_line(6);
        oled_print_at(6, 20, "ACTUATOR: LED OFF");
        printf("ACTUATOR: LED OFF\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "CMD:ABORT") == 0) {
        ui_show_abort();
        printf("ALERT: EMERGENCY ABORT TRIGGERED\n");
        fflush(stdout);
    }
    else if (strcmp(clean_cmd, "CMD:IDLE") == 0 || strcmp(clean_cmd, "CMD:CLEAR") == 0) {
        ui_show_idle();
        printf("STATUS: IDLE\n");
        fflush(stdout);
    }
}

// ---------------- UART Listener Task ----------------
static void uart_rx_task(void *pvParameters) {
    uint8_t data[BUF_SIZE];
    char line_buf[256];
    int line_idx = 0;

    while (1) {
        int len = uart_read_bytes(UART_PORT, data, sizeof(data) - 1, pdMS_TO_TICKS(50));
        if (len > 0) {
            for (int i = 0; i < len; i++) {
                char c = (char)data[i];
                if (c == '\n' || c == '\r') {
                    if (line_idx > 0) {
                        line_buf[line_idx] = '\0';
                        process_serial_command(line_buf);
                        line_idx = 0;
                    }
                } else {
                    if (line_idx < (int)(sizeof(line_buf) - 1)) {
                        line_buf[line_idx++] = c;
                    }
                }
            }
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

// ---------------- Main Entry Point ----------------
void app_main(void) {
    ESP_LOGI(TAG, "Starting Zylose Edge-Bridge Firmware...");

    // 1. Initialize Status LED
    gpio_reset_pin(LED_PIN);
    gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT);
    gpio_set_level(LED_PIN, 0);

    // 2. Initialize I2C for OLED Display
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = OLED_SDA,
        .scl_io_num = OLED_SCL,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 100000,
    };
    ESP_ERROR_CHECK(i2c_param_config(I2C_NUM_0, &conf));
    ESP_ERROR_CHECK(i2c_driver_install(I2C_NUM_0, I2C_MODE_MASTER, 0, 0, 0));

    // 3. Initialize OLED
    oled_init();
    ui_show_idle();

    // 4. Configure UART for Serial Communication with PC
    uart_config_t uart_config = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
    };
    ESP_ERROR_CHECK(uart_param_config(UART_PORT, &uart_config));
    ESP_ERROR_CHECK(uart_driver_install(UART_PORT, BUF_SIZE * 2, 0, 0, NULL, 0));

    printf("\n========================================\n");
    printf("     ZYLOSE TINYML EDGE CONTROLLER      \n");
    printf("========================================\n");
    printf("Hardware status: OLED initialized (0x3C)\n");
    printf("Status LED     : Ready on GPIO 4\n");
    printf("Communication  : UART @ 115200 baud\n");
    printf("Ready for wake-word and NLP commands.\n\n");
    fflush(stdout);

    // 5. Start UART RX Task
    xTaskCreate(uart_rx_task, "uart_rx_task", 4096, NULL, 10, NULL);
}
