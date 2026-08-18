#ifndef BUTTON_INPUT_H
#define BUTTON_INPUT_H

#include <stdint.h>

#define BUTTON_FORWARD_MASK         (1U << 0)
#define BUTTON_BACKWARD_MASK        (1U << 1)
#define BUTTON_LEFT_MASK            (1U << 2)
#define BUTTON_RIGHT_MASK           (1U << 3)

#define BUTTON_GRIPPER1_OPEN_MASK    (1U << 4)
#define BUTTON_GRIPPER1_CLOSE_MASK   (1U << 5)
#define BUTTON_GRIPPER2_OPEN_MASK    (1U << 6)
#define BUTTON_GRIPPER2_CLOSE_MASK   (1U << 7)

void ButtonInput_Init(void);
void ButtonInput_Update(void);
uint8_t ButtonInput_GetState(void);

#endif
