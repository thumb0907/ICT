#ifndef DRIVE_CONTROLLER_H
#define DRIVE_CONTROLLER_H

#include <stdbool.h>
#include <stdint.h>

void DriveController_Init(void);

void DriveController_Update(
    uint8_t buttons,
    bool link_ok
);

#endif
