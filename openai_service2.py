from openai import OpenAI
import json
import streamlit as st


def generate_anomaly_report(sensor_data):
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        client = OpenAI(api_key=api_key)

        system_prompt = """
        당신은 도금 및 크로메이트 표면처리 공정의 15년 차 QA/QC 전문가이자 EHS 관리자입니다.
        당신의 임무는 실시간 센서 이상 데이터를 분석하여, 물리/화학적 원리(농도, pH, 전기전도도, 온도, 반응속도 등)에 기반한 정확한 원인 진단과 즉시 실행 가능한 SOP(표준작업지침)를 작성하는 것입니다.

        [엄격한 작성 규칙]
        1. 근본 원인(Root Cause): 반드시 "가장 유력한 실제 공정 원인 1개" + "센서 오류 가능성 1개"로 분리하여 진단하십시오.
        2. 조치 지시의 구조: 즉각 조치는 반드시 "안전 확보(PPE) → 물리적 행동 → 대기 시간" 순서로 작성하며, 후속 단계는 "재측정 목표값 → 실패 시 2차 보고(Escalation)"로 명확히 나누어 작성하십시오.
        3. 약품 투입 기준: 절대량(ml, L)이 아닌 비율(%) 또는 단계 규정량으로 작성하십시오.
        4. 공정 변수별 대응 기준:
           - pH: 조절제 투입 및 순환 펌프 가동
           - 온도: 열교환기/히터 출력 제어 및 냉각수 밸브 확인
           - 전압/전류: 정류기 설정값 조정 및 접점 확인
        """

        user_prompt = f"""
        다음 공정 데이터를 분석하여 JSON 리포트를 작성하십시오.

        [현재 공정 상태 요약]
        - 대상 공정: {sensor_data.get('process_name', '크로메이트 (Chromate)')}
        - 설비 용량: {sensor_data.get('tank_volume', 1500)}L
        - 발생 알람: {sensor_data.get('alarm_type', '알 수 없음')}
        - 측정 수치: {sensor_data.get('current_value')} {sensor_data.get('unit')}
        - 정상 범위: {sensor_data.get('low_limit')} ~ {sensor_data.get('high_limit')} {sensor_data.get('unit')}
        - 해당 변수 추세: {sensor_data.get('trend', '데이터 없음')}
        - 타 변수 현재 상태: {sensor_data.get('other_sensors_status', '데이터 없음')}
        - 최근 30분 내 조치 이력: {sensor_data.get('recent_actions', '없음')}
        """

        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "anomaly_report",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "AI_Report": {
                                "type": "object",
                                "properties": {
                                    "Issue": {"type": "string"},
                                    "Root_Cause": {
                                        "type": "object",
                                        "properties": {
                                            "Process_Cause": {"type": "string"},
                                            "Sensor_Cause": {"type": "string"}
                                        },
                                        "required": ["Process_Cause", "Sensor_Cause"],
                                        "additionalProperties": False
                                    },
                                    "Corrective_Action": {"type": "string"},
                                    "Verification_Escalation": {"type": "string"},
                                    "Preventive_Action": {"type": "string"},
                                    "Confidence_Score": {"type": "integer"}
                                },
                                "required": [
                                    "Issue",
                                    "Root_Cause",
                                    "Corrective_Action",
                                    "Verification_Escalation",
                                    "Preventive_Action",
                                    "Confidence_Score"
                                ],
                                "additionalProperties": False
                            }
                        },
                        "required": ["AI_Report"],
                        "additionalProperties": False
                    }
                }
            }
        )

        if not getattr(response, "output_text", None):
            return {"error": f"AI 응답 텍스트가 비어 있습니다. raw response={response}"}

        parsed = json.loads(response.output_text)

        if "AI_Report" not in parsed:
            return {"error": f"AI 응답 형식이 예상과 다릅니다: {parsed}"}

        return parsed

    except json.JSONDecodeError as e:
        return {"error": f"AI 응답을 JSON으로 해석하지 못했습니다: {str(e)}"}
    except Exception as e:
        return {"error": f"OpenAI API 호출 중 오류가 발생했습니다: {str(e)}"}