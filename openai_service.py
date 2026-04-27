from openai import OpenAI
import json

# ⭐ 괄호 안에 sensor_data 딱 하나만 있도록 수정된 완벽한 버전입니다.
def generate_anomaly_report(sensor_data): 
    """
    OpenAI API를 호출하여 이상 탐지 원인 분석 및 SOP 리포트를 JSON 형태로 반환합니다.
    """
    
    # OpenAI 클라이언트 초기화 (하드코딩된 API 키 사용)
    client = OpenAI(api_key="")

    # 1. 시스템 프롬프트
    system_prompt = """
    당신은 도금 및 크로메이트 표면처리 공정의 15년 차 QA/QC 전문가이자 EHS 관리자입니다.
    당신의 임무는 실시간 센서 이상 데이터를 분석하여, 물리/화학적 원리(농도, pH, 전기전도도, 온도, 반응속도 등)에 기반한 정확한 원인 진단과 즉시 실행 가능한 SOP(표준작업지침)를 작성하는 것입니다.

    [엄격한 작성 규칙]
    1. 근본 원인(Root Cause): 반드시 "가장 유력한 실제 공정 원인 1개" + "센서 오류(드리프트, 오염, 단선 등) 가능성 1개"로 분리하여 진단하십시오.
    2. 조치 지시의 구조: 즉각 조치는 반드시 "안전 확보(PPE) → 물리적 행동 → 대기 시간" 순서로 작성하며, 후속 단계는 "재측정 목표값 → 실패 시 2차 보고(Escalation)"로 명확히 나누어 작성하십시오.
    3. 약품 투입 기준: 화학 약품(산/알칼리 등) 투입량은 탱크 용량을 고려하여 임의의 절대량(ml, L)이 아닌 "전체 용량 대비 비율(%)" 또는 "사전 정의된 1단계 규정량(Step 1 Dosing)"으로 지시하십시오.
    4. 공정 변수별 대응 기준:
       - pH: 조절제 투입 및 순환 펌프 가동
       - 온도: 열교환기/히터 출력 제어 및 냉각수 밸브 확인
       - 전압/전류: 정류기(Rectifier) 설정값 조정 및 접점 확인

    [출력 형식 절대 준수]
    (json)이나 추가적인 설명 없이, 오직 아래의 유효한 JSON 포맷으로만 출력하십시오.
    {
      "AI_Report": {
        "Issue": "(발생 알람 및 현재 수치 명시)",
        "Root_Cause": {
          "Process_Cause": "(가장 유력한 공정 원인 1개)",
          "Sensor_Cause": "(계측기/센서 오류 가능성 1개)"
        },
        "Corrective_Action": "(안전 보호구 명시, 구체적 행동 지침 및 대기 시간)",
        "Verification_Escalation": "(재측정 목표 수치 및 달성 실패 시 라인 정지 등 2차 조치)",
        "Preventive_Action": "(ISO 규격에 맞춘 점검 주기 또는 캘리브레이션 계획)",
        "Confidence_Score": (0~100 사이의 정수)
      }
    }
    """

    # 2. 유저 프롬프트
    user_prompt = f"""
    다음 공정 데이터를 분석하여 JSON 리포트를 작성하십시오.

    [현재 공정 상태 요약]
    - 대상 공정: {sensor_data.get('process_name', '크로메이트 (Chromate)')} (설비 용량: {sensor_data.get('tank_volume', 1500)}L)
    - 발생 알람: {sensor_data.get('alarm_type', '알 수 없음')}
    - 측정 수치: {sensor_data.get('current_value')} {sensor_data.get('unit')} (정상 범위: {sensor_data.get('low_limit')} ~ {sensor_data.get('high_limit')} {sensor_data.get('unit')})
    - 해당 변수 추세: {sensor_data.get('trend', '데이터 없음')}
    - 타 변수 현재 상태: {sensor_data.get('other_sensors_status', '데이터 없음')}
    - 최근 30분 내 조치 이력: {sensor_data.get('recent_actions', '없음')}
    """

    try:
        # API 호출
        response = client.chat.completions.create(
            model="gpt-4o", 
            response_format={"type": "json_object"},
            temperature=0.2, 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        result_text = response.choices[0].message.content
        return json.loads(result_text)

    except Exception as e:
        return {"error": f"OpenAI API 호출 중 오류가 발생했습니다: {str(e)}"}