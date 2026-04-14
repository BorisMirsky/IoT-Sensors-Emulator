import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RuleType(Enum):
    SET_TARGET = "set_target"
    ADD_OFFSET = "add_offset"
    PUBLISH_ALERT = "publish_alert"
    CHANGE_INTERVAL = "change_interval"


@dataclass
class BehaviorRule:
    """Одно правило поведения"""
    type: RuleType
    condition: Optional[Dict[str, Any]]  # условие срабатывания
    action: Dict[str, Any]  # действие при срабатывании


class BehaviorScript:
    """
    Сценарий поведения устройства на основе JSON-правил.
    Пример правил:
    {
        "rules": [
            {
                "type": "set_target",
                "condition": {"simulated_time": "> 60"},
                "action": {"sensor": "temperature", "value": 25.0}
            },
            {
                "type": "set_target",
                "condition": {"simulated_time": "> 120"},
                "action": {"sensor": "temperature", "value": 22.0}
            },
            {
                "type": "add_offset",
                "condition": {"sensor": "temperature", "value": "> 30"},
                "action": {"sensor": "temperature", "offset": -2.0}
            }
        ]
    }
    """

    def __init__(self, rules: List[Dict[str, Any]]):
        self.rules = []
        for rule_dict in rules:
            rule_type = RuleType(rule_dict.get("type"))
            rule = BehaviorRule(
                type=rule_type,
                condition=rule_dict.get("condition"),
                action=rule_dict.get("action", {})
            )
            self.rules.append(rule)

    def evaluate(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Оценить все правила и вернуть список действий, которые нужно выполнить.
        
        Args:
            context: Словарь с текущим состоянием:
                - simulated_time: текущее симулированное время
                - sensor_values: {sensor_name: value}
                - last_command: последняя полученная команда (если есть)
        
        Returns:
            Список действий для выполнения
        """
        actions = []
        
        for rule in self.rules:
            if self._check_condition(rule.condition, context):
                actions.append(rule.action)
                logger.debug(f"Rule triggered: {rule.type.value} -> {rule.action}")
        
        return actions

    def _check_condition(self, condition: Optional[Dict[str, Any]], context: Dict[str, Any]) -> bool:
        """Проверить, выполняется ли условие"""
        if condition is None:
            return True  # правило без условия срабатывает всегда
        
        for key, value in condition.items():
            if key == "simulated_time":
                if not self._check_time_condition(value, context.get("simulated_time", 0)):
                    return False
            elif key == "sensor":
                # Ожидается: {"sensor": "temperature", "value": "> 30"}
                sensor_name = value.get("sensor")
                operator = value.get("operator", ">")
                threshold = value.get("value")
                
                sensor_val = context.get("sensor_values", {}).get(sensor_name)
                if sensor_val is None:
                    return False
                
                if not self._check_comparison(sensor_val, operator, threshold):
                    return False
            elif key == "command":
                # Проверка команды (например, {"command": "heater_on"})
                last_cmd = context.get("last_command")
                if last_cmd != value:
                    return False
            else:
                # Прямое сравнение значений в контексте
                if context.get(key) != value:
                    return False
        
        return True

    def _check_time_condition(self, condition: Any, current_time: float) -> bool:
        """Проверить временное условие (например: "> 60" или "between 10 and 20")"""
        if isinstance(condition, str):
            # Простое условие: "> 60", "< 100", "= 50"
            for op in [">=", "<=", ">", "<", "==", "="]:
                if condition.startswith(op):
                    try:
                        value = float(condition[len(op):].strip())
                        if op == ">":
                            return current_time > value
                        elif op == "<":
                            return current_time < value
                        elif op == ">=":
                            return current_time >= value
                        elif op == "<=":
                            return current_time <= value
                        elif op in ("==", "="):
                            return current_time == value
                    except ValueError:
                        pass
        elif isinstance(condition, dict) and "between" in condition:
            # Диапазон: {"between": [10, 20]}
            values = condition["between"]
            if len(values) == 2:
                return values[0] <= current_time <= values[1]
        
        return False

    def _check_comparison(self, value: float, operator: str, threshold: float) -> bool:
        """Сравнить значение с порогом"""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator in ("==", "="):
            return value == threshold
        return False


def load_behavior_from_file(file_path: str) -> Optional[BehaviorScript]:
    """Загрузить сценарий поведения из JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rules = data.get("rules", [])
        if not rules:
            logger.warning(f"No rules found in {file_path}")
            return None
        
        return BehaviorScript(rules)
    except Exception as e:
        logger.error(f"Failed to load behavior from {file_path}: {e}")
        return None