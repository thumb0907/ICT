#include "status_led.h"
#include "main.h"

#define DRIVE_BUTTON_MASK    0x0FU
#define GRIPPER_BUTTON_MASK  0xF0U

void StatusLed_Init(void)
{
    HAL_GPIO_WritePin(
        LED_LINK_GPIO_Port,
        LED_LINK_Pin,
        GPIO_PIN_RESET
    );

    HAL_GPIO_WritePin(
        LED_DRIVE_GPIO_Port,
        LED_DRIVE_Pin,
        GPIO_PIN_RESET
    );

    HAL_GPIO_WritePin(
        LED_GRIPPER_GPIO_Port,
        LED_GRIPPER_Pin,
        GPIO_PIN_RESET
    );
}

void StatusLed_Update(
    uint8_t button_state,
    bool link_ok
)
{
    if (!link_ok)
    {
        HAL_GPIO_WritePin(
            LED_LINK_GPIO_Port,
            LED_LINK_Pin,
            GPIO_PIN_RESET
        );

        HAL_GPIO_WritePin(
            LED_DRIVE_GPIO_Port,
            LED_DRIVE_Pin,
            GPIO_PIN_RESET
        );

        HAL_GPIO_WritePin(
            LED_GRIPPER_GPIO_Port,
            LED_GRIPPER_Pin,
            GPIO_PIN_RESET
        );

        return;
    }

    HAL_GPIO_WritePin(
        LED_LINK_GPIO_Port,
        LED_LINK_Pin,
        GPIO_PIN_SET
    );

    HAL_GPIO_WritePin(
        LED_DRIVE_GPIO_Port,
        LED_DRIVE_Pin,
        ((button_state & DRIVE_BUTTON_MASK) != 0U)
            ? GPIO_PIN_SET
            : GPIO_PIN_RESET
    );

    HAL_GPIO_WritePin(
        LED_GRIPPER_GPIO_Port,
        LED_GRIPPER_Pin,
        ((button_state & GRIPPER_BUTTON_MASK) != 0U)
            ? GPIO_PIN_SET
            : GPIO_PIN_RESET
    );
}
