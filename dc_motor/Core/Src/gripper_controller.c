#include "gripper_controller.h"
#include "gripper_servo.h"

#define BUTTON_GRIPPER1_OPEN   (1U << 4)
#define BUTTON_GRIPPER1_CLOSE  (1U << 5)
#define BUTTON_GRIPPER2_OPEN   (1U << 6)
#define BUTTON_GRIPPER2_CLOSE  (1U << 7)

/*
 * 아래 값은 초기 시험값이다.
 * 기구물에 맞게 반드시 다시 측정해야 한다.
 */
#define GRIPPER1_OPEN_US       1450U
#define GRIPPER1_CLOSE_US      1550U

#define GRIPPER2_OPEN_US       1550U
#define GRIPPER2_CLOSE_US      1450U

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

void GripperController_Init(void)
{
    gripper1_last_pulse = 0U;
    gripper2_last_pulse = 0U;

    /*
     * 첫 그리퍼 명령을 받기 전에는
     * PWM을 출력하지 않는다.
     */
    GripperServo_DisableAll();
}

void GripperController_Update(
    uint8_t buttons,
    bool link_ok
)
{
    uint8_t gripper1_buttons;
    uint8_t gripper2_buttons;

    /*
     * 통신 단절 시 새로운 움직임을 만들지 않고
     * 마지막 위치를 유지한다.
     */
    if (!link_ok)
    {
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
             * 버튼 없음 또는 열기/닫기 동시 입력:
             * 마지막 위치 유지
             */
            break;
    }

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
            break;
    }
}
