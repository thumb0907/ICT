#include "gripper_controller.h"
#include "gripper_servo.h"

#define BUTTON_GRIPPER1_OPEN   (1U << 4)
#define BUTTON_GRIPPER1_CLOSE  (1U << 5)
#define BUTTON_GRIPPER2_OPEN   (1U << 6)
#define BUTTON_GRIPPER2_CLOSE  (1U << 7)

/*
 * 실제 기구물에 맞게 보정할 값
 */
#define GRIPPER1_OPEN_US       1180U
#define GRIPPER1_CLOSE_US      780U

#define GRIPPER2_OPEN_US   1180U
#define GRIPPER2_CLOSE_US   780U

static uint16_t gripper1_last_pulse;
static uint16_t gripper2_last_pulse;

static void GripperController_Set1(
    uint16_t pulse_us
)
{
    if (pulse_us == gripper1_last_pulse)
    {
        return;
    }

    GripperServo_Set1PulseUs(pulse_us);
    gripper1_last_pulse = pulse_us;
}

static void GripperController_Set2(
    uint16_t pulse_us
)
{
    if (pulse_us == gripper2_last_pulse)
    {
        return;
    }

    GripperServo_Set2PulseUs(pulse_us);
    gripper2_last_pulse = pulse_us;
}

static void GripperController_Disable1(void)
{
    if (gripper1_last_pulse == 0U)
    {
        return;
    }

    GripperServo_Disable1();
    gripper1_last_pulse = 0U;
}

static void GripperController_Disable2(void)
{
    if (gripper2_last_pulse == 0U)
    {
        return;
    }

    GripperServo_Disable2();
    gripper2_last_pulse = 0U;
}

void GripperController_Init(void)
{
    gripper1_last_pulse = 0U;
    gripper2_last_pulse = 0U;

    GripperServo_DisableAll();
}

void GripperController_Update(
    uint8_t buttons,
    bool link_ok
)
{
    uint8_t gripper1_buttons;
    uint8_t gripper2_buttons;

    if (!link_ok)
    {
        GripperController_Disable1();
        GripperController_Disable2();
        return;
    }

    gripper1_buttons =
        buttons
        & (BUTTON_GRIPPER1_OPEN
           | BUTTON_GRIPPER1_CLOSE);

    gripper2_buttons =
        buttons
        & (BUTTON_GRIPPER2_OPEN
           | BUTTON_GRIPPER2_CLOSE);

    /*
     * 그리퍼 1:
     * 버튼을 누르는 동안만 PWM 출력
     */
    switch (gripper1_buttons)
    {
        case BUTTON_GRIPPER1_OPEN:
            GripperController_Set1(
                GRIPPER1_OPEN_US
            );
            break;

        case BUTTON_GRIPPER1_CLOSE:
            GripperController_Set1(
                GRIPPER1_CLOSE_US
            );
            break;

        default:
            /*
             * 버튼을 놓았거나
             * 열기·닫기를 동시에 누른 경우
             */
            GripperController_Disable1();
            break;
    }

    /*
     * 그리퍼 2:
     * 버튼을 누르는 동안만 PWM 출력
     */
    switch (gripper2_buttons)
    {
        case BUTTON_GRIPPER2_OPEN:
            GripperController_Set2(
                GRIPPER2_OPEN_US
            );
            break;

        case BUTTON_GRIPPER2_CLOSE:
            GripperController_Set2(
                GRIPPER2_CLOSE_US
            );
            break;

        default:
            GripperController_Disable2();
            break;
    }
}
