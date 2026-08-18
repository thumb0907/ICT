#ifndef COMMAND_PROTOCOL_H
#define COMMAND_PROTOCOL_H

#include "stm32f4xx_hal.h"
#include <stdint.h>

#define COMMAND_PACKET_START  0xAAU
#define COMMAND_PACKET_END    0x55U
#define COMMAND_PACKET_SIZE   5U

void CommandProtocol_Init(void);

HAL_StatusTypeDef CommandProtocol_SendButtons(
    uint8_t button_state
);

#endif
