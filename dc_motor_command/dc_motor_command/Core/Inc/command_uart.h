#ifndef COMMAND_UART_H
#define COMMAND_UART_H

#include "stm32f4xx_hal.h"

void CommandUart_Init(UART_HandleTypeDef *huart);

HAL_StatusTypeDef CommandUart_SendText(const char *text);

HAL_StatusTypeDef CommandUart_SendBytes(
    const uint8_t *data,
    uint16_t size
);

#endif
