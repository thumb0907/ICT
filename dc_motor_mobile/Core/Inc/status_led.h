#ifndef STATUS_LED_H
#define STATUS_LED_H

#include <stdbool.h>
#include <stdint.h>

void StatusLed_Init(void);

void StatusLed_Update(
    uint8_t button_state,
    bool link_ok
);

#endif
