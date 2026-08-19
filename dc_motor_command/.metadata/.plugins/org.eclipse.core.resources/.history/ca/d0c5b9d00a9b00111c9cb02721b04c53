#include "drive_controller.h"
#include "motor_driver.h"

#define BUTTON_FORWARD       (1U << 0)
#define BUTTON_BACKWARD      (1U << 1)
#define BUTTON_LEFT          (1U << 2)
#define BUTTON_RIGHT         (1U << 3)

#define DRIVE_BUTTON_MASK    0x0FU
#define DRIVE_TEST_SPEED     200

static int16_t last_left_speed;
static int16_t last_right_speed;

static void DriveController_Apply(
    int16_t left_speed,
    int16_t right_speed
)
{
    if (left_speed != last_left_speed)
    {
        MotorDriver_SetLeft(left_speed);
        last_left_speed = left_speed;
    }

    if (right_speed != last_right_speed)
    {
        MotorDriver_SetRight(right_speed);
        last_right_speed = right_speed;
    }
}

void DriveController_Init(void)
{
    last_left_speed = 0;
    last_right_speed = 0;

    MotorDriver_Stop();
}

void DriveController_Update(
    uint8_t buttons,
    bool link_ok
)
{
    int16_t left_speed = 0;
    int16_t right_speed = 0;
    uint8_t drive_buttons;

    if (!link_ok)
    {
        DriveController_Apply(0, 0);
        return;
    }

    drive_buttons = buttons & DRIVE_BUTTON_MASK;

    switch (drive_buttons)
    {
        case BUTTON_FORWARD:
            left_speed = DRIVE_TEST_SPEED;
            right_speed = DRIVE_TEST_SPEED;
            break;

        case BUTTON_BACKWARD:
            left_speed = -DRIVE_TEST_SPEED;
            right_speed = -DRIVE_TEST_SPEED;
            break;

        case BUTTON_LEFT:
            left_speed = -DRIVE_TEST_SPEED;
            right_speed = DRIVE_TEST_SPEED;
            break;

        case BUTTON_RIGHT:
            left_speed = DRIVE_TEST_SPEED;
            right_speed = -DRIVE_TEST_SPEED;
            break;

        default:
            /*
             * 버튼을 누르지 않았거나 이동 버튼을
             * 동시에 여러 개 누른 경우 정지한다.
             */
            left_speed = 0;
            right_speed = 0;
            break;
    }

    DriveController_Apply(
        left_speed,
        right_speed
    );
}
