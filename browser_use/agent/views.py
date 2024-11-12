from __future__ import annotations

from inspect import signature
from typing import Any, Callable, ClassVar, Dict, Optional, Type

from pydantic import BaseModel, ConfigDict, create_model

from browser_use.controller.views import (
	ClickElementControllerAction,
	ControllerActions,
	InputTextControllerAction,
)


class AgentState(BaseModel):
	valuation_previous_goal: str
	memory: str
	next_goal: str


class ActionResult(BaseModel):
	done: bool
	extracted_content: Optional[str] = None
	error: Optional[str] = None


class CustomAction(BaseModel):
	"""Base model for custom actions"""

	name: str
	description: str
	prompt_description: str = ''

	# Store function outside of model fields
	_function: ClassVar[Dict[str, Callable]] = {}

	model_config = ConfigDict(arbitrary_types_allowed=True)

	def __init__(self, description: str, function: Callable, **kwargs):
		# Generate prompt description before super().__init__
		sig = signature(function)
		params = {name: param.annotation.__name__ for name, param in sig.parameters.items()}
		param_str = ', '.join(f'"{k}": "{v}"' for k, v in params.items())
		prompt_desc = f'- {description}:\n{{"{function.__name__}": {{{param_str}}}}}'

		# Store function in class variable
		self._function[function.__name__] = function

		super().__init__(
			name=function.__name__,
			description=description,
			prompt_description=prompt_desc,
			**kwargs,
		)

	def execute(self, params: dict) -> ActionResult:
		try:
			# Use stored function
			func = self._function[self.name]
			result = func(**params)
			return ActionResult(done=False, extracted_content=str(result) if result else None)
		except Exception as e:
			return ActionResult(done=False, error=str(e))


class DynamicActions(BaseModel):
	"""Base class that combines controller and custom actions"""

	_cached_model: ClassVar[Optional[Type[DynamicActions]]] = None
	_custom_actions: ClassVar[Dict[str, CustomAction]] = {}  # Store custom actions

	@classmethod
	def get_or_create_model(
		cls, custom_actions: Optional[list[CustomAction]] = None
	) -> Type[DynamicActions]:
		if cls._cached_model is None:
			# Store custom actions for later use
			cls._custom_actions = {action.name: action for action in (custom_actions or [])}

			# Get all fields from ControllerActions
			controller_fields = {
				name: (field.annotation, field.default)
				for name, field in ControllerActions.model_fields.items()
			}

			# Add custom action fields at the same level
			custom_fields = {
				action.name: (Optional[Dict[str, Any]], None) for action in (custom_actions or [])
			}

			# Combine all fields
			all_fields = {**controller_fields, **custom_fields}

			# Create the combined model
			cls._cached_model = create_model('DynamicActions', __base__=cls, **all_fields)

		return cls._cached_model

	def is_controller_action(self) -> bool:
		"""Check if any controller action is set"""
		return any(
			getattr(self, field_name) is not None for field_name in ControllerActions.model_fields
		)

	def is_custom_action(self) -> bool:
		"""Check if any custom action is set"""
		return any(getattr(self, action_name) is not None for action_name in self._custom_actions)

	def get_custom_action_and_params(self) -> tuple[CustomAction, dict]:
		"""Get the active custom action and its parameters"""
		for action_name, action in self._custom_actions.items():
			params = getattr(self, action_name)
			if params is not None:
				return action, params
		raise ValueError('No custom action found')


class AgentAction(DynamicActions, ControllerActions):
	"""Concrete implementation of combined actions"""

	pass


class ClickElementControllerHistoryItem(ClickElementControllerAction):
	xpath: str | None


class InputTextControllerHistoryItem(InputTextControllerAction):
	xpath: str | None


class AgentHistory(AgentAction):
	click_element: Optional[ClickElementControllerHistoryItem] = None
	input_text: Optional[InputTextControllerHistoryItem] = None
	url: str


class DynamicOutput:
	"""Factory for creating Output models with dynamic actions"""

	_cached_model: ClassVar[Optional[Type[BaseModel]]] = None

	@classmethod
	def get_or_create_model(cls, action_model: Type[DynamicActions]) -> Type[BaseModel]:
		if cls._cached_model is None:
			# Create the combined action type that includes both dynamic and controller actions
			combined_action = create_model(
				'CombinedAction',
				__base__=(action_model, ControllerActions),  # Inherit from both
			)

			# Create the output model with the combined action type
			cls._cached_model = create_model(
				'Output',
				current_state=(AgentState, ...),
				action=(combined_action, ...),  # Use combined action type
			)

		return cls._cached_model
