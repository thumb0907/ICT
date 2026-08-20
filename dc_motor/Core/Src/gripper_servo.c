#include "gripper_servo.h"

static TIM_HandleTypeDef *servo_timer;

static uint16_t GripperServo_ClampPulse(
    uint16_t pulse_us
)
{
    if (pulse_us < GRIPPER_SERVO_MIN_US)
    {
        return GRIPPER_SERVO_MIN_US;
    }

    if (pulse_us > GRIPPER_SERVO_MAX_US)
    {
        return GRIPPER_SERVO_MAX_US;
    }

    return pulse_us;
}

static void GripperServo_SetPulse(
    uint32_t channel,
    uint16_t pulse_us
)
{
    if (servo_timer == NULL)
    {
        return;
    }

    pulse_us = GripperServo_ClampPulse(pulse_us);

    /*
     * TIM4의 1카운트가 1us이므로
     * pulse_us 값을 CCR에 바로 사용한다.
     */
    __HAL_TIM_SET_COMPARE(
        servo_timer,
        channel,
        pulse_us
    );
}

HAL_StatusTypeDef GripperServo_Init(
    TIM_HandleTypeDef *htim
)
{
    if (htim == NULL)
    {
        return HAL_ERROR;
    }

    servo_timer = htim;

    /*
     * 서보 모델과 기구물의 안전 각도를 확인하기 전까지
     * PWM Pulse를 0으로 유지한다.
     */
    __HAL_TIM_SET_COMPARE(
        servo_timer,
        TIM_CHANNEL_3,
        0U
    );

    __HAL_TIM_SET_COMPARE(
        servo_timer,
        TIM_CHANNEL_4,
        0U
    );

    if (HAL_TIM_PWM_Start(
            servo_timer,
            TIM_CHANNEL_3
        ) != HAL_OK)
    {
        return HAL_ERROR;
    }

    if (HAL_TIM_PWM_Start(
            servo_timer,
            TIM_CHANNEL_4
        ) != HAL_OK)
    {
        HAL_TIM_PWM_Stop(
            servo_timer,
            TIM_CHANNEL_3
        );

        return HAL_ERROR;
    }

    return HAL_OK;
}

void GripperServo_Set1PulseUs(uint16_t pulse_us)
{
    GripperServo_SetPulse(
        TIM_CHANNEL_3,
        pulse_us
    );
}

void GripperServo_Set2PulseUs(uint16_t pulse_us)
{
    GripperServo_SetPulse(
        TIM_CHANNEL_4,
        pulse_us
    );
}

void GripperServo_SetNeutralAll(void)
{
    GripperServo_Set1PulseUs(
        GRIPPER_SERVO_NEUTRAL_US
    );

    GripperServo_Set2PulseUs(
        GRIPPER_SERVO_NEUTRAL_US
    );
}

void GripperServo_DisableAll(void)
{
    if (servo_timer == NULL)
    {
        return;
    }

    __HAL_TIM_SET_COMPARE(
        servo_timer,
        TIM_CHANNEL_3,
        0U
    );

    __HAL_TIM_SET_COMPARE(
        servo_timer,
        TIM_CHANNEL_4,
        0U
    );
}
