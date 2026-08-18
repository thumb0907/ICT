#include "command_protocol.h"
#include "command_uart.h"

static uint8_t sequence_number;

static uint8_t CommandProtocol_CalculateCrc8(
    const uint8_t *data,
    uint16_t size
)
{
    uint8_t crc = 0U;

    for (uint16_t index = 0U; index < size; index++)
    {
        crc ^= data[index];

        for (uint8_t bit = 0U; bit < 8U; bit++)
        {
            if ((crc & 0x80U) != 0U)
            {
                crc = (uint8_t)((crc << 1U) ^ 0x07U);
            }
            else
            {
                crc <<= 1U;
            }
        }
    }

    return crc;
}

void CommandProtocol_Init(void)
{
    sequence_number = 0U;
}

HAL_StatusTypeDef CommandProtocol_SendButtons(
    uint8_t button_state
)
{
    uint8_t packet[COMMAND_PACKET_SIZE];
    uint8_t crc_data[2];
    HAL_StatusTypeDef result;

    packet[0] = COMMAND_PACKET_START;
    packet[1] = sequence_number;
    packet[2] = button_state;

    crc_data[0] = packet[1];
    crc_data[1] = packet[2];

    packet[3] = CommandProtocol_CalculateCrc8(
        crc_data,
        sizeof(crc_data)
    );

    packet[4] = COMMAND_PACKET_END;

    result = CommandUart_SendBytes(
        packet,
        sizeof(packet)
    );

    if (result == HAL_OK)
    {
        sequence_number++;
    }

    return result;
}
