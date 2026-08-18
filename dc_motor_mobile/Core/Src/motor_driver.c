#include "motor_driver.h"
#include "main.h"

#define LEFT_FORWARD_LEVEL   GPIO_PIN_SET
#define RIGHT_FORWARD_LEVEL  GPIO_PIN_SET

static TIM_HandleTypeDef *motor_timer;

static int16_t MotorDriver_ClampSpeed(int16_t speed)
{
    if (speed > MOTOR_SPEED_MAX)
    {
        return MOTOR_SPEED_MAX;
    }

    if (speed < -MOTOR_SPEED_MAX)
    {
        return -MOTOR_SPEED_MAX;
    }

    return speed;
}

static void MotorDriver_SetChannel(
    uint32_t channel,
    GPIO_TypeDef *direction_port,
    uint16_t direction_pin,
    GPIO_PinState forward_level,
    int16_t speed
)
{
    uint16_t magnitude;
    uint32_t timer_period;
    uint32_t compare;
    GPIO_PinState direction_level;

    if (motor_timer == NULL)
    {
        return;
    }

    speed = MotorDriver_ClampSpeed(speed);

    /*
     * 방향을 변경하기 전에 PWM을 먼저 0으로 만든다.
     */
    __HAL_TIM_SET_COMPARE(
        motor_timer,
        channel,
        0U
    );

    if (speed == 0)
    {
        return;
    }

    if (speed > 0)
    {
        magnitude = (uint16_t)speed;
        direction_level = forward_level;
    }
    else
    {
        magnitude = (uint16_t)(-speed);

        direction_level =
            (forward_level == GPIO_PIN_SET)
                ? GPIO_PIN_RESET
                : GPIO_PIN_SET;
    }

    HAL_GPIO_WritePin(
        direction_port,
        direction_pin,
        direction_level
    );

    timer_period =
        __HAL_TIM_GET_AUTORELOAD(motor_timer) + 1U;

    compare =
        ((uint32_t)magnitude * timer_period)
        / MOTOR_SPEED_MAX;

    __HAL_TIM_SET_COMPARE(
        motor_timer,
        channel,
        compare
    );
}

HAL_StatusTypeDef MotorDriver_Init(
    TIM_HandleTypeDef *htim
)
{
    if (htim == NULL)
    {
        return HAL_ERROR;
    }

    motor_timer = htim;

    __HAL_TIM_SET_COMPARE(
        motor_timer,
        TIM_CHANNEL_1,
        0U
    );

    __HAL_TIM_SET_COMPARE(
        motor_timer,
        TIM_CHANNEL_2,
        0U
    );

    HAL_GPIO_WritePin(
        MOTOR_LEFT_DIR_GPIO_Port,
        MOTOR_LEFT_DIR_Pin,
        GPIO_PIN_RESET
    );

    HAL_GPIO_WritePin(
        MOTOR_RIGHT_DIR_GPIO_Port,
        MOTOR_RIGHT_DIR_Pin,
        GPIO_PIN_RESET
    );

    if (HAL_TIM_PWM_Start(
            motor_timer,
            TIM_CHANNEL_1
        ) != HAL_OK)
    {
        return HAL_ERROR;
    }

    if (HAL_TIM_PWM_Start(
            motor_timer,
            TIM_CHANNEL_2
        ) != HAL_OK)
    {
        return HAL_ERROR;
    }

    return HAL_OK;
}

void MotorDriver_SetLeft(int16_t speed)
{
    MotorDriver_SetChannel(
        TIM_CHANNEL_1,
        MOTOR_LEFT_DIR_GPIO_Port,
        MOTOR_LEFT_DIR_Pin,
        LEFT_FORWARD_LEVEL,
        speed
    );
}

void MotorDriver_SetRight(int16_t speed)
{
    MotorDriver_SetChannel(
        TIM_CHANNEL_2,
        MOTOR_RIGHT_DIR_GPIO_Port,
        MOTOR_RIGHT_DIR_Pin,
        RIGHT_FORWARD_LEVEL,
        speed
    );
}

void MotorDriver_Stop(void)
{
    if (motor_timer == NULL)
    {
        return;
    }

    __HAL_TIM_SET_COMPARE(
        motor_timer,
        TIM_CHANNEL_1,
        0U
    );

    __HAL_TIM_SET_COMPARE(
        motor_timer,
        TIM_CHANNEL_2,
        0U
    );
}
