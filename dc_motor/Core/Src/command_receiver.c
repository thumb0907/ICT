#include "command_receiver.h"

#define COMMAND_PACKET_START  0xAAU
#define COMMAND_PACKET_END    0x55U
#define COMMAND_PACKET_SIZE   5U

static UART_HandleTypeDef *receiver_uart;

static uint8_t receive_byte;
static uint8_t receive_packet[COMMAND_PACKET_SIZE];
static uint8_t receive_index;

static volatile uint8_t latest_buttons;
static volatile uint8_t latest_sequence;
static volatile uint32_t last_valid_tick;
static volatile bool command_received;

static uint8_t CommandReceiver_CalculateCrc8(
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

static void CommandReceiver_StartReceive(void)
{
    if (receiver_uart == NULL)
    {
        return;
    }

    HAL_UART_Receive_IT(
        receiver_uart,
        &receive_byte,
        1U
    );
}

static void CommandReceiver_ProcessByte(uint8_t data)
{
    uint8_t crc_data[2];
    uint8_t calculated_crc;

    if (receive_index == 0U)
    {
        if (data == COMMAND_PACKET_START)
        {
            receive_packet[0] = data;
            receive_index = 1U;
        }

        return;
    }

    receive_packet[receive_index] = data;
    receive_index++;

    if (receive_index < COMMAND_PACKET_SIZE)
    {
        return;
    }

    if (receive_packet[4] == COMMAND_PACKET_END)
    {
        crc_data[0] = receive_packet[1];
        crc_data[1] = receive_packet[2];

        calculated_crc = CommandReceiver_CalculateCrc8(
            crc_data,
            sizeof(crc_data)
        );

        if (calculated_crc == receive_packet[3])
        {
            latest_sequence = receive_packet[1];
            latest_buttons = receive_packet[2];
            last_valid_tick = HAL_GetTick();
            command_received = true;
        }
    }

    receive_index = 0U;

    /*
     * 현재 바이트가 다음 패킷의 시작값일 가능성을 처리한다.
     */
    if (data == COMMAND_PACKET_START)
    {
        receive_packet[0] = data;
        receive_index = 1U;
    }
}

void CommandReceiver_Init(UART_HandleTypeDef *huart)
{
    receiver_uart = huart;

    receive_byte = 0U;
    receive_index = 0U;

    latest_buttons = 0U;
    latest_sequence = 0U;
    last_valid_tick = 0U;
    command_received = false;

    CommandReceiver_StartReceive();
}

void CommandReceiver_HandleRxComplete(
    UART_HandleTypeDef *huart
)
{
    if (huart != receiver_uart)
    {
        return;
    }

    CommandReceiver_ProcessByte(receive_byte);
    CommandReceiver_StartReceive();
}

void CommandReceiver_HandleError(
    UART_HandleTypeDef *huart
)
{
    if (huart != receiver_uart)
    {
        return;
    }

    receive_index = 0U;
    CommandReceiver_StartReceive();
}

uint8_t CommandReceiver_GetButtons(void)
{
    return latest_buttons;
}

uint8_t CommandReceiver_GetSequence(void)
{
    return latest_sequence;
}

bool CommandReceiver_HasReceivedCommand(void)
{
    return command_received;
}

bool CommandReceiver_IsTimedOut(
    uint32_t now_ms,
    uint32_t timeout_ms
)
{
    if (!command_received)
    {
        return true;
    }

    return ((uint32_t)(now_ms - last_valid_tick) >= timeout_ms);
}
