#include "I2S.h"

void I2S_Init( i2s_mode_t MODE, int SAMPLE_RATE,  i2s_bits_per_sample_t BPS) {
  const i2s_config_t i2s_config = {
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = BPS, // I2S_BITS_PER_SAMPLE_16BIT or I2S_BITS_PER_SAMPLE_32BIT
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,      // L/R to high - left, L/R to ground - right channel
    .communication_format = (i2s_comm_format_t)(I2S_COMM_FORMAT_I2S | I2S_COMM_FORMAT_I2S_MSB),
    .intr_alloc_flags = 0, // default interrupt priority
    //.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pin_config;
  pin_config.bck_io_num = PIN_I2S_BCLK;
  pin_config.ws_io_num = PIN_I2S_LRC;

  if (MODE == I2S_MODE_RX) {
    pin_config.data_out_num = I2S_PIN_NO_CHANGE;
    pin_config.data_in_num = PIN_I2S_DIN;
  }
  else if (MODE == I2S_MODE_TX) {
    pin_config.data_out_num = PIN_I2S_DOUT;
    pin_config.data_in_num = I2S_PIN_NO_CHANGE;
  }

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
  //最终设置: 16k, 16位，单声道
  //1.0.3 rc1 以后的版本不要调用下句，否则I2S不可用
  //i2s_set_clk(I2S_NUM_0, SAMPLE_RATE, BPS, I2S_CHANNEL_MONO);
}

int I2S_Read(char* data, int numData) {
  size_t bytesIn = 0;
  esp_err_t result = i2s_read(I2S_NUM_0, (char *)data, numData,  &bytesIn, portMAX_DELAY);
  return bytesIn;
}

void I2S_Write(char* data, int numData) {
  //   i2s_write_bytes(I2S_NUM_0, (const char *)data, numData, portMAX_DELAY);
}

void I2S_uninstall()
{
  i2s_driver_uninstall(I2S_NUM_0);
}
