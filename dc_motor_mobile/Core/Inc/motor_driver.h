#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

#include "stm32f4xx_hal.h"

#include <stdint.h>

#define MOTOR_SPEED_MAX  1000

HAL_StatusTypeDef MotorDriver_Init(
    TIM_HandleTypeDef *htim
);

void MotorDriver_SetLeft(int16_t speed);

void MotorDriver_SetRight(int16_t speed);

void MotorDriver_Stop(void);

#endif
