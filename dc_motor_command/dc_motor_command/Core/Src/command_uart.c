#include "command_uart.h"

#include <stddef.h>
#include <string.h>

static UART_HandleTypeDef *command_uart = NULL;

void CommandUart_Init(UART_HandleTypeDef *huart)
{
    command_uart = huart;
}

HAL_StatusTypeDef CommandUart_SendText(const char *text)
{
    if ((command_uart == NULL) || (text == NULL))
    {
        return HAL_ERROR;
    }

    return HAL_UART_Transmit(
        command_uart,
        (uint8_t *)text,
        (uint16_t)strlen(text),
        100
    );
}
HAL_StatusTypeDef CommandUart_SendBytes(
    const uint8_t *data,
    uint16_t size
)
{
    if ((command_uart == NULL) ||
        (data == NULL) ||
        (size == 0U))
    {
        return HAL_ERROR;
    }

    return HAL_UART_Transmit(
        command_uart,
        (uint8_t *)data,
        size,
        100
    );
}
