#ifndef GRIPPER_SERVO_H
#define GRIPPER_SERVO_H

#include "stm32f4xx_hal.h"

#include <stdint.h>

#define GRIPPER_SERVO_MIN_US       1000U
#define GRIPPER_SERVO_NEUTRAL_US   1500U
#define GRIPPER_SERVO_MAX_US       2000U

HAL_StatusTypeDef GripperServo_Init(
    TIM_HandleTypeDef *htim
);

void GripperServo_Set1PulseUs(uint16_t pulse_us);
void GripperServo_Set2PulseUs(uint16_t pulse_us);

void GripperServo_SetNeutralAll(void);
void GripperServo_DisableAll(void);

#endif
