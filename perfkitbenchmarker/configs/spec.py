# Copyright 2015 PerfKitBenchmarker Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Base class for objects decoded from a YAML config."""

import collections
import threading
from typing import Any, Optional

from absl import flags
from perfkitbenchmarker import errors
from perfkitbenchmarker import provider_info
from perfkitbenchmarker.configs import option_decoders
import six


_SPEC_REGISTRY = {}


def GetSpecClass(base_class, **kwargs) -> 'BaseSpecMetaClass':
  """Returns the subclass with the corresponding attributes.

  Args:
    base_class: The base class of the resource to return (e.g. BaseVmSpec).
    **kwargs: Every attribute/value of the subclass's ATTRS that were used to
      register the subclass.

  Raises:
    Exception: If no class could be found with matching attributes.
  """
  key = [base_class.__name__]
  key += sorted(kwargs.items())
  return _SPEC_REGISTRY.get(tuple(key), base_class)


class BaseSpecMetaClass(type):
  """Metaclass that allows each BaseSpec derived class to have its own decoders."""

  # The name of the spec class that will be extended with auto-registered
  # subclasses.
  SPEC_TYPE = None
  # A list of the attributes that are used to register the subclasses.
  SPEC_ATTRS = ['CLOUD']

  def __init__(cls, name, bases, dct):
    super().__init__(name, bases, dct)
    cls._init_decoders_lock = threading.Lock()
    cls._decoders = collections.OrderedDict()
    cls._required_options = set()
    if all(hasattr(cls, attr) for attr in cls.SPEC_ATTRS) and cls.SPEC_TYPE:
      key = [cls.SPEC_TYPE]
      key += sorted([(attr, getattr(cls, attr)) for attr in cls.SPEC_ATTRS])
      if tuple(key) in _SPEC_REGISTRY:
        raise errors.Config.InvalidValue(
            'Subclasses of %s must define unique values for the attrs: %s.'
            % (cls.SPEC_TYPE, cls.SPEC_ATTRS)
        )
      _SPEC_REGISTRY[tuple(key)] = cls


class BaseSpec(six.with_metaclass(BaseSpecMetaClass, object)):
  """Object decoded from a YAML config."""

  # Each derived class has its own copy of the following three variables. They
  # are initialized by BaseSpecMetaClass.__init__ and later populated by
  # _InitDecoders when the first instance of the derived class is created.
  _init_decoders_lock = None  # threading.Lock that protects the next two vars.
  _decoders = None  # dict mapping config option name to ConfigOptionDecoder.
  _required_options = None  # set of strings. Required config options.

  def __init__(
      self,
      component_full_name: str,
      flag_values: Optional[flags.FlagValues] = None,
      **kwargs: Any
  ):
    """Initializes a BaseSpec.

    Translates keyword arguments via the class's decoders and assigns the
    corresponding instance attribute. Derived classes can register decoders
    for additional attributes by overriding _GetOptionDecoderConstructions
    and can add support for additional flags by overriding _ApplyFlags.

    Args:
      component_full_name: string. Fully qualified name of the configurable
        component containing the config options.
      flag_values: None or flags.FlagValues. Runtime flags that may override the
        provided config option values in kwargs.
      **kwargs: dict mapping config option names to provided values.

    Raises:
      errors.Config.MissingOption: If a config option is required, but a value
          was not provided in kwargs.
      errors.Config.UnrecognizedOption: If an unrecognized config option is
          provided with a value in kwargs.
    """
    if not self._decoders:
      self._InitDecoders()
    if flag_values:
      self._ApplyFlags(kwargs, flag_values)
    missing_options = self._required_options.difference(kwargs)
    if missing_options:
      raise errors.Config.MissingOption(
          'Required options were missing from {0}: {1}.'.format(
              component_full_name, ', '.join(sorted(missing_options))
          )
      )
    unrecognized_options = frozenset(kwargs).difference(self._decoders)
    if unrecognized_options:
      raise errors.Config.UnrecognizedOption(
          'Unrecognized options were found in {0}: {1}.'.format(
              component_full_name, ', '.join(sorted(unrecognized_options))
          )
      )
    self._DecodeAndInit(
        component_full_name, kwargs, self._decoders, flag_values
    )

  @classmethod
  def _InitDecoders(cls):
    """Creates a ConfigOptionDecoder for each config option.

    Populates cls._decoders and cls._required_options.
    """
    with cls._init_decoders_lock:
      if not cls._decoders:
        constructions = cls._GetOptionDecoderConstructions()
        for option, decoder_construction in sorted(
            six.iteritems(constructions)
        ):
          decoder_class, init_args = decoder_construction
          decoder = decoder_class(option=option, **init_args)
          cls._decoders[option] = decoder
          if decoder.required:
            cls._required_options.add(option)

  @classmethod
  def _ApplyFlags(
      cls, config_values: dict[str, Any], flag_values: flags.FlagValues
  ):
    """Modifies config options based on runtime flag values.

    Can be overridden by derived classes to add support for specific flags.

    Args:
      config_values: dict mapping config option names to provided values. May be
        modified by this function.
      flag_values: flags.FlagValues. Runtime flags that may override the
        provided config values.
    """
    pass

  @classmethod
  def _GetOptionDecoderConstructions(cls):
    """Gets decoder classes and constructor args for each configurable option.

    Can be overridden by derived classes to add options or impose additional
    requirements on existing options.

    Returns:
      dict. Maps option name string to a (ConfigOptionDecoder class, dict) pair.
          The pair specifies a decoder class and its __init__() keyword
          arguments to construct in order to decode the named option.
    """
    return {}

  def _DecodeAndInit(
      self,
      component_full_name: str,
      config: dict[str, Any],
      decoders: collections.OrderedDict[
          str, option_decoders.ConfigOptionDecoder
      ],
      flag_values: Optional[flags.FlagValues],
  ):
    """Initializes spec attributes from provided config option values.

    Args:
      component_full_name: string. Fully qualified name of the configurable
        component containing the config options.
      config: dict mapping option name string to option value.
      decoders: OrderedDict mapping option name string to ConfigOptionDecoder.
      flag_values: flags.FlagValues. Runtime flags that may override provided
        config option values. These flags have already been applied to the
        current config, but they may be passed to the decoders for propagation
        to deeper spec constructors.
    """
    assert isinstance(decoders, collections.OrderedDict), (
        'decoders must be an OrderedDict. The order in which options are '
        'decoded must be guaranteed.'
    )
    for option, decoder in six.iteritems(decoders):
      if option in config:
        value = decoder.Decode(config[option], component_full_name, flag_values)
      else:
        value = decoder.default
      setattr(self, option, value)


class PerCloudConfigSpec(BaseSpec):
  """Contains one config dict attribute per cloud provider.

  The name of each attribute is the name of the cloud provider.
  """

  @classmethod
  def _GetOptionDecoderConstructions(cls):
    """Gets decoder classes and constructor args for each configurable option.

    Returns:
      dict. Maps option name string to a (ConfigOptionDecoder class, dict) pair.
      The pair specifies a decoder class and its __init__() keyword arguments
      to construct in order to decode the named option.
    """
    result = super()._GetOptionDecoderConstructions()
    for cloud in provider_info.VALID_CLOUDS:
      result[cloud] = option_decoders.TypeVerifier, {
          'default': None,
          'valid_types': (dict,),
      }
    return result


class PerCloudConfigDecoder(option_decoders.TypeVerifier):
  """Decodes the disk_spec or vm_spec option of a VM group config object."""

  def __init__(self, **kwargs):
    super().__init__(valid_types=(dict,), **kwargs)

  def Decode(self, value, component_full_name, flag_values):
    """Decodes the disk_spec or vm_spec option of a VM group config object.

    Args:
      value: None or dict mapping cloud provider name string to a dict.
      component_full_name: string. Fully qualified name of the configurable
        component containing the config option.
      flag_values: flags.FlagValues. Runtime flag values to be propagated to
        BaseSpec constructors.

    Returns:
      _PerCloudConfigSpec decoded from the input dict.
    """
    input_dict = super().Decode(value, component_full_name, flag_values)
    if input_dict is None:
      return None
    return PerCloudConfigSpec(
        self._GetOptionFullName(component_full_name),
        flag_values=flag_values,
        **input_dict
    )
