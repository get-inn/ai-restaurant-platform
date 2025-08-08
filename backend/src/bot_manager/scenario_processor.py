"""
Scenario Processor for Bot Management System

This module is responsible for:
1. Evaluating dialog scenario steps
2. Processing user inputs against scenario definitions
3. Determining the next step in a conversation flow
4. Resolving conditional logic in scenarios
5. Validating user input against scenario rules
"""

from typing import Dict, Any, List, Optional, Union, Callable
import logging
import re
import json
from datetime import datetime

from src.bot_manager.conversation_logger import get_logger, LogEventType

# Configure logging
logger = logging.getLogger(__name__)


class ScenarioProcessor:
    """
    Processes bot dialog scenarios and manages conversation flow logic.
    """

    def __init__(self, custom_conditions: Dict[str, Callable] = None):
        """
        Initialize the scenario processor.
        
        Args:
            custom_conditions: Optional dictionary of custom condition evaluator functions
        """
        self.custom_conditions = custom_conditions or {}
        self.logger = get_logger()
        
    def process_step(
        self,
        scenario_data: Dict[str, Any],
        current_step_id: str,
        collected_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a step in the scenario.
        
        Args:
            scenario_data: The complete scenario definition
            current_step_id: The ID of the current step to process
            collected_data: User data collected so far
            
        Returns:
            A dictionary containing the processed step information
        """
        steps = scenario_data.get("steps", {})
        result = {
            "current_step_id": current_step_id,
            "message": None,
            "buttons": None,
            "expected_input": None,
            "next_step_id": None,
            "error": None
        }
        
        # Find the current step
        current_step = None
        if isinstance(steps, list):
            for step in steps:
                if step.get("id") == current_step_id:
                    current_step = step
                    break
        elif isinstance(steps, dict):
            current_step = steps.get(current_step_id)
        
        if not current_step:
            error_msg = f"Step not found: {current_step_id}"
            result["error"] = error_msg
            self.logger.error(LogEventType.ERROR, error_msg)
            return result
            
        # Process the step based on its type
        step_type = current_step.get("type", "message")
        
        self.logger.debug(LogEventType.SCENARIO, f"Processing step '{current_step_id}' of type '{step_type}'", {
            "step_id": current_step_id,
            "step_type": step_type,
            "has_media": "media" in current_step.get("message", {})
        })
        
        if step_type == "message":
            # Process a simple message step
            message = current_step.get("message", {})
            message_text = message.get("text", "")
            
            # Process variable substitutions in the text
            message_text = self._substitute_variables(message_text, collected_data, scenario_data)
            
            self.logger.debug(LogEventType.SCENARIO, f"Generated message text: '{message_text[:50]}...'" if len(message_text) > 50 else f"Generated message text: '{message_text}'")
            
            # Add processed message to result
            media = message.get("media", [])
            result["message"] = {
                "text": message_text,
                "media": media
            }
            
            # Log media details if present
            if media:
                self.logger.debug(LogEventType.SCENARIO, f"Message contains {len(media)} media items", {
                    "media_count": len(media),
                    "media_types": [item.get("type") for item in media],
                    "media_ids": [item.get("file_id") for item in media],
                    "step_id": current_step_id
                })
            
            # Add buttons if present
            if "buttons" in current_step:
                result["buttons"] = current_step.get("buttons", [])
                
            # Add expected input if present
            if "expected_input" in current_step:
                result["expected_input"] = current_step.get("expected_input")
                
            # Determine next step
            next_step_id = self._resolve_next_step(current_step, collected_data)
            result["next_step_id"] = next_step_id
            
            if next_step_id:
                self.logger.debug(LogEventType.SCENARIO, f"Next step resolved to: '{next_step_id}'")
            else:
                self.logger.debug(LogEventType.SCENARIO, "No next step resolved (conversation may end)")
            
        elif step_type == "conditional_message":
            # Process a conditional message step
            conditions = current_step.get("conditions", [])
            for condition in conditions:
                if self._evaluate_condition(condition.get("if", ""), collected_data):
                    message = condition.get("message", {})
                    message_text = message.get("text", "")
                    
                    # Process variable substitutions in the text
                    message_text = self._substitute_variables(message_text, collected_data, scenario_data)
                    
                    # Add processed message to result
                    media = message.get("media", [])
                    result["message"] = {
                        "text": message_text,
                        "media": media
                    }
                    
                    # Log media details if present
                    if media:
                        self.logger.debug(LogEventType.SCENARIO, f"Conditional message contains {len(media)} media items", {
                            "media_count": len(media),
                            "media_types": [item.get("type") for item in media],
                            "media_ids": [item.get("file_id") for item in media],
                            "step_id": current_step_id,
                            "condition_matched": condition.get("if", "")
                        })
                    break
            
            # Add buttons if present in the step (not the condition)
            if "buttons" in current_step:
                result["buttons"] = current_step.get("buttons", [])
                
            # Add expected input if present
            if "expected_input" in current_step:
                result["expected_input"] = current_step.get("expected_input")
                
            # Determine next step
            next_step_id = self._resolve_next_step(current_step, collected_data)
            result["next_step_id"] = next_step_id
            
            if next_step_id:
                self.logger.debug(LogEventType.SCENARIO, f"Next step resolved to: '{next_step_id}'")
            else:
                self.logger.debug(LogEventType.SCENARIO, "No next step resolved (conversation may end)")
        
        elif step_type == "action":
            # For action steps, just determine the next step
            # Real action processing would be done by other components
            result["next_step_id"] = self._resolve_next_step(current_step, collected_data)
            
        else:
            error_msg = f"Unsupported step type: {step_type}"
            result["error"] = error_msg
            self.logger.error(LogEventType.ERROR, error_msg)
        
        return result
    
    def validate_user_input(
        self,
        user_input: Any,
        expected_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate user input against the expected input definition.
        
        Args:
            user_input: The input provided by the user
            expected_input: Definition of what input is expected
            
        Returns:
            Dictionary with validation result and any error messages
        """
        if not expected_input:
            self.logger.debug(LogEventType.PROCESSING, "No validation rules defined, input accepted")
            return {"valid": True}
            
        input_type = expected_input.get("type", "text")
        validation = expected_input.get("validation", {})
        
        self.logger.debug(LogEventType.PROCESSING, 
                         f"Validating input as type '{input_type}'", 
                         {"user_input": str(user_input)[:50] if isinstance(user_input, str) else str(user_input)})
        
        result = {
            "valid": True,
            "error": None,
            "processed_value": user_input
        }
        
        if input_type == "text":
            if not isinstance(user_input, str):
                result["valid"] = False
                result["error"] = "Expected text input"
                self.logger.debug(LogEventType.PROCESSING, "Validation failed: Expected text input")
                return result
                
            # Check if there's a pattern to validate against
            if "pattern" in validation:
                pattern = validation.get("pattern")
                if not re.match(pattern, user_input):
                    result["valid"] = False
                    error_message = validation.get("error_message", "Input format is not valid")
                    result["error"] = error_message
                    self.logger.debug(LogEventType.PROCESSING, f"Validation failed: {error_message}", 
                                    {"pattern": pattern, "input": user_input})
                    return result
                    
            # Check for minimum/maximum length
            min_length = validation.get("min_length")
            if min_length is not None and len(user_input) < min_length:
                result["valid"] = False
                error_message = validation.get("min_length_error", f"Input must be at least {min_length} characters")
                result["error"] = error_message
                self.logger.debug(LogEventType.PROCESSING, f"Validation failed: {error_message}", 
                                {"min_length": min_length, "actual_length": len(user_input)})
                return result
                
            max_length = validation.get("max_length")
            if max_length is not None and len(user_input) > max_length:
                result["valid"] = False
                error_message = validation.get("max_length_error", f"Input must not exceed {max_length} characters")
                result["error"] = error_message
                self.logger.debug(LogEventType.PROCESSING, f"Validation failed: {error_message}", 
                                {"max_length": max_length, "actual_length": len(user_input)})
                return result
                
        elif input_type == "number":
            try:
                num_value = float(user_input)
                result["processed_value"] = num_value
                
                # Check for minimum/maximum values
                min_value = validation.get("min_value")
                if min_value is not None and num_value < min_value:
                    result["valid"] = False
                    error_message = validation.get("min_value_error", f"Value must be at least {min_value}")
                    result["error"] = error_message
                    self.logger.debug(LogEventType.PROCESSING, f"Validation failed: {error_message}", 
                                    {"min_value": min_value, "actual_value": num_value})
                    return result
                    
                max_value = validation.get("max_value")
                if max_value is not None and num_value > max_value:
                    result["valid"] = False
                    error_message = validation.get("max_value_error", f"Value must not exceed {max_value}")
                    result["error"] = error_message
                    self.logger.debug(LogEventType.PROCESSING, f"Validation failed: {error_message}", 
                                    {"max_value": max_value, "actual_value": num_value})
                    return result
            except (ValueError, TypeError):
                result["valid"] = False
                result["error"] = "Invalid number format"
                self.logger.debug(LogEventType.PROCESSING, "Validation failed: Invalid number format", 
                                {"input": user_input})
                return result
                
        elif input_type == "button":
            # For button inputs, typically the value is predefined, so less validation is needed
            # We might want to check that the value is one of the allowed options
            allowed_values = validation.get("allowed_values", [])
            if allowed_values and user_input not in allowed_values:
                result["valid"] = False
                error_message = validation.get("error_message", "Invalid option selected")
                result["error"] = error_message
                self.logger.debug(LogEventType.PROCESSING, f"Validation failed: {error_message}", 
                                {"allowed_values": allowed_values, "actual_value": user_input})
                return result
                
        elif input_type == "date":
            try:
                # Try to parse the date
                date_format = validation.get("format", "%Y-%m-%d")
                date_value = datetime.strptime(user_input, date_format)
                result["processed_value"] = date_value.strftime("%Y-%m-%d")
            except ValueError:
                result["valid"] = False
                error_message = validation.get("error_message", "Invalid date format")
                result["error"] = error_message
                self.logger.debug(LogEventType.PROCESSING, f"Validation failed: {error_message}", 
                                {"expected_format": date_format, "actual_value": user_input})
                return result
                
        # If we got here, validation passed
        self.logger.debug(LogEventType.PROCESSING, "Input validation successful")
        return result
    
    def _substitute_variables(
        self,
        text: str,
        collected_data: Dict[str, Any],
        scenario_data: Dict[str, Any]
    ) -> str:
        """
        Replace variable placeholders in text with their values.
        
        Args:
            text: The text containing variable placeholders
            collected_data: Dictionary of collected user data
            scenario_data: The complete scenario definition
            
        Returns:
            Text with variables replaced by their values
        """
        if not text:
            return ""
            
        # Regular expression to match variables like {{variable_name}}
        pattern = r'{{(\w+)}}'
        
        def replace_var(match):
            var_name = match.group(1)
            if var_name not in collected_data:
                return f"{{{{{var_name}}}}}"  # Keep the original if variable not found
                
            var_value = collected_data[var_name]
            
            # Check for mapping in scenario
            variables_mapping = scenario_data.get("variables_mapping", {})
            if var_name in variables_mapping and str(var_value) in variables_mapping[var_name]:
                mapped_value = str(variables_mapping[var_name][str(var_value)])
                self.logger.debug(LogEventType.VARIABLE, f"Variable '{var_name}' mapped from '{var_value}' to '{mapped_value}'")
                return mapped_value
            
            self.logger.debug(LogEventType.VARIABLE, f"Variable '{var_name}' substituted with value '{var_value}'")
            return str(var_value)
            
        return re.sub(pattern, replace_var, text)
    
    def _resolve_next_step(
        self,
        current_step: Dict[str, Any],
        collected_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Determine the next step ID based on current step definition and conditions.
        
        Args:
            current_step: The current step definition
            collected_data: User data collected so far
            
        Returns:
            The ID of the next step, or None if not determinable
        """
        next_step = current_step.get("next_step")
        
        if not next_step:
            return None
            
        # If next_step is just a string, that's the ID of the next step
        if isinstance(next_step, str):
            return next_step
            
        # If next_step is a dict, it might be a conditional next step
        if isinstance(next_step, dict):
            next_type = next_step.get("type")
            
            if next_type == "conditional":
                conditions = next_step.get("conditions", [])
                
                for condition in conditions:
                    condition_expr = condition.get("if", "")
                    result = self._evaluate_condition(condition_expr, collected_data)
                    then_step = condition.get("then")
                    
                    self.logger.debug(LogEventType.CONDITION, 
                                     f"Next step condition '{condition_expr}' evaluated to {result}", 
                                     {"next_step": then_step if result else "(not taken)"})
                    
                    if result:
                        return then_step
                        
                # If no conditions match, check for an else clause
                if "else" in next_step:
                    else_step = next_step.get("else")
                    self.logger.debug(LogEventType.CONDITION, 
                                     "No conditions matched, using 'else' path", 
                                     {"next_step": else_step})
                    return else_step
        
        return None
    
    def _evaluate_condition(
        self,
        condition_expr: str,
        collected_data: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a condition expression against the collected data.
        
        Args:
            condition_expr: The condition expression to evaluate
            collected_data: User data collected so far
            
        Returns:
            True if the condition evaluates to true, False otherwise
        """
        if not condition_expr:
            self.logger.debug(LogEventType.CONDITION, "Empty condition expression, evaluating to FALSE")
            return False
            
        # Check for custom condition evaluator
        if condition_expr in self.custom_conditions:
            result = self.custom_conditions[condition_expr](collected_data)
            self.logger.debug(LogEventType.CONDITION, 
                             f"Custom condition '{condition_expr}' evaluated to {result}")
            return result
            
        # Handle basic equality comparison (var == value)
        if "==" in condition_expr:
            left, right = condition_expr.split("==", 1)
            left = left.strip()
            right = right.strip()
            
            # Remove quotes from right side if it's a string literal
            if (right.startswith("'") and right.endswith("'")) or \
               (right.startswith('"') and right.endswith('"')):
                right = right[1:-1]
                
            # Get the actual value from collected data
            left_value = collected_data.get(left)
            
            # Compare and return result
            return str(left_value) == right
            
        # Handle inequality comparison (var != value)
        elif "!=" in condition_expr:
            left, right = condition_expr.split("!=", 1)
            left = left.strip()
            right = right.strip()
            
            # Remove quotes from right side if it's a string literal
            if (right.startswith("'") and right.endswith("'")) or \
               (right.startswith('"') and right.endswith('"')):
                right = right[1:-1]
                
            # Get the actual value from collected data
            left_value = collected_data.get(left)
            
            # Compare and return result
            return str(left_value) != right
            
        # Handle greater than comparison (var > value)
        elif ">" in condition_expr:
            left, right = condition_expr.split(">", 1)
            left = left.strip()
            right = right.strip()
            
            try:
                # Convert to numbers for comparison
                left_value = float(collected_data.get(left, 0))
                right_value = float(right)
                return left_value > right_value
            except (ValueError, TypeError):
                return False
                
        # Handle less than comparison (var < value)
        elif "<" in condition_expr:
            left, right = condition_expr.split("<", 1)
            left = left.strip()
            right = right.strip()
            
            try:
                # Convert to numbers for comparison
                left_value = float(collected_data.get(left, 0))
                right_value = float(right)
                return left_value < right_value
            except (ValueError, TypeError):
                return False
                
        # Handle contains check (var contains value)
        elif "contains" in condition_expr:
            left, right = condition_expr.split("contains", 1)
            left = left.strip()
            right = right.strip()
            
            # Remove quotes from right side if it's a string literal
            if (right.startswith("'") and right.endswith("'")) or \
               (right.startswith('"') and right.endswith('"')):
                right = right[1:-1]
                
            # Get the actual value from collected data
            left_value = str(collected_data.get(left, ""))
            
            return right in left_value
            
        # Handle exists check (var exists)
        elif "exists" in condition_expr:
            var_name = condition_expr.split("exists", 1)[0].strip()
            return var_name in collected_data
            
        logger.warning(f"Unsupported condition: {condition_expr}")
        return False