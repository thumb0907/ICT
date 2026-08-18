#include "button_input.h"
#include "main.h"

#define DEBOUNCE_REQUIRED_COUNT  3U

static uint8_t stable_state;
static uint8_t candidate_state;
static uint8_t candidate_count;

static uint8_t ButtonInput_ReadRaw(void)
{
    uint8_t state = 0;

    if (HAL_GPIO_ReadPin(BTN_FORWARD_GPIO_Port,
                        BTN_FORWARD_Pin) == GPIO_PIN_RESET)
    {
        state |= BUTTON_FORWARD_MASK;
    }

    if (HAL_GPIO_ReadPin(BTN_BACKWARD_GPIO_Port,
                        BTN_BACKWARD_Pin) == GPIO_PIN_RESET)
    {
        state |= BUTTON_BACKWARD_MASK;
    }

    if (HAL_GPIO_ReadPin(BTN_LEFT_GPIO_Port,
                        BTN_LEFT_Pin) == GPIO_PIN_RESET)
    {
        state |= BUTTON_LEFT_MASK;
    }

    if (HAL_GPIO_ReadPin(BTN_RIGHT_GPIO_Port,
                        BTN_RIGHT_Pin) == GPIO_PIN_RESET)
    {
        state |= BUTTON_RIGHT_MASK;
    }

    if (HAL_GPIO_ReadPin(BTN_GRIPPER1_OPEN_GPIO_Port,
                        BTN_GRIPPER1_OPEN_Pin) == GPIO_PIN_RESET)
    {
        state |= BUTTON_GRIPPER1_OPEN_MASK;
    }

    if (HAL_GPIO_ReadPin(BTN_GRIPPER1_CLOSE_GPIO_Port,
                        BTN_GRIPPER1_CLOSE_Pin) == GPIO_PIN_RESET)
    {
        state |= BUTTON_GRIPPER1_CLOSE_MASK;
    }

    if (HAL_GPIO_ReadPin(BTN_GRIPPER2_OPEN_GPIO_Port,
                        BTN_GRIPPER2_OPEN_Pin) == GPIO_PIN_RESET)
    {
        state |= BUTTON_GRIPPER2_OPEN_MASK;
    }

    if (HAL_GPIO_ReadPin(BTN_GRIPPER2_CLOSE_GPIO_Port,
                        BTN_GRIPPER2_CLOSE_Pin) == GPIO_PIN_RESET)
    {
        state |= BUTTON_GRIPPER2_CLOSE_MASK;
    }

    return state;
}

void ButtonInput_Init(void)
{
    stable_state = ButtonInput_ReadRaw();
    candidate_state = stable_state;
    candidate_count = 0;
}

void ButtonInput_Update(void)
{
    uint8_t raw_state = ButtonInput_ReadRaw();

    if (raw_state != candidate_state)
    {
        candidate_state = raw_state;
        candidate_count = 0;
        return;
    }

    if (candidate_count < DEBOUNCE_REQUIRED_COUNT)
    {
        candidate_count++;
    }

    if (candidate_count >= DEBOUNCE_REQUIRED_COUNT)
    {
        stable_state = candidate_state;
    }
}

uint8_t ButtonInput_GetState(void)
{
    return stable_state;
}
