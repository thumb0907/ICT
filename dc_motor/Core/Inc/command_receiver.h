#ifndef COMMAND_RECEIVER_H
#define COMMAND_RECEIVER_H

#include "stm32f4xx_hal.h"

#include <stdbool.h>
#include <stdint.h>

void CommandReceiver_Init(UART_HandleTypeDef *huart);

void CommandReceiver_HandleRxComplete(
    UART_HandleTypeDef *huart
);

void CommandReceiver_HandleError(
    UART_HandleTypeDef *huart
);

uint8_t CommandReceiver_GetButtons(void);

uint8_t CommandReceiver_GetSequence(void);

bool CommandReceiver_HasReceivedCommand(void);

bool CommandReceiver_IsTimedOut(
    uint32_t now_ms,
    uint32_t timeout_ms
);

#endif
