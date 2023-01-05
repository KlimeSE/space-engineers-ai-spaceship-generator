from datetime import datetime
from enum import Enum
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pcgsepy.config import BIN_POP_SIZE, CS_MAX_AGE, N_EMITTER_STEPS
from pcgsepy.mapelites.behaviors import (BehaviorCharacterization, avg_ma,
                                         mame, mami, symmetry)

from pcgsepy.mapelites.map import MAPElites


class Semaphore:
    def __init__(self,
                 locked: bool = False) -> None:
        """Create a `Semamphore` object.

        Args:
            locked (bool, optional): Initial locked value. Defaults to False.
        """
        self._is_locked = locked
        self._running = ''
    
    @property
    def is_locked(self) -> bool:
        """Check if the semaphore is currently locked.

        Returns:
            bool: The locked value.
        """
        return self._is_locked
    
    def lock(self,
             name: Optional[str] = '') -> None:
        """Lock the semaphore.

        Args:
            name (Optional[str], optional): The locking process name. Defaults to ''.
        """
        self._is_locked = True
        self._running = name
    
    def unlock(self) -> None:
        """Unlock the semaphore"""
        self._is_locked = False
        self._running = ''


class DashLoggerHandler(logging.StreamHandler):
    def __init__(self):
        """Create a new logging handler.
        """
        logging.StreamHandler.__init__(self)
        self.queue = []

    def emit(self,
             record: Any) -> None:
        """Process the incoming record.

        Args:
            record (Any): The new logging record.
        """
        t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = self.format(record)
        self.queue.append(f'[{t}]\t{msg}')


class AppMode(Enum):
    """Enumerator for the application mode."""
    USER = 1
    DEV = 2


class AppSettings:
    def __init__(self) -> None:
        """Generate a new `AppSettings` object."""
        self.current_mapelites: Optional[MAPElites] = None
        self.gen_counter: int = 0
        self.hm_callback_props: Dict[str, Any] = {}
        self.behavior_descriptors: List[BehaviorCharacterization] = [
            BehaviorCharacterization(name='Major axis / Medium axis',
                                    func=mame,
                                    bounds=(0, 10)),
            BehaviorCharacterization(name='Major axis / Smallest axis',
                                    func=mami,
                                    bounds=(0, 20)),
            BehaviorCharacterization(name='Average Proportions',
                                    func=avg_ma,
                                    bounds=(0, 20)),
            BehaviorCharacterization(name='Symmetry',
                                    func=symmetry,
                                    bounds=(0, 1))
        ]
        self.rngseed = uuid.uuid4().int
        self.selected_bins: List[Tuple[int, int]] = []
        self.step_progress: int = -1
        self.use_custom_colors: bool = True
        self.app_mode: AppMode = None
        self.emitter_steps: int = N_EMITTER_STEPS
        self.symmetry: Optional[str] = None
        self.safe_mode: bool = True
        self.voxelised: bool = False

    def initialize(self,
                   mapelites: MAPElites,
                   dev_mode: bool = False):
        """Initialize the object.

        Args:
            mapelites (MAPElites): The MAP-Elites object.
            dev_mode (bool, optional): Whether to set the application to developer mode. Defaults to False.
        """
        self.current_mapelites = mapelites
        self.app_mode = AppMode.DEV if dev_mode else AppMode.USER
        self.hm_callback_props['pop'] = {
            'Feasible': 'feasible',
            'Infeasible': 'infeasible'
        }
        self.hm_callback_props['metric'] = {
            'Fitness': {
                'name': 'fitness',
                'zmax': {
                    'feasible': sum([x.weight * x.bounds[1] for x in self.current_mapelites.feasible_fitnesses]) + self.current_mapelites.nsc,
                    'infeasible': 1.
                },
                'colorscale': 'Inferno'
            },
            'Age':  {
                'name': 'age',
                'zmax': {
                    'feasible': CS_MAX_AGE,
                    'infeasible': CS_MAX_AGE
                },
                'colorscale': 'Aggrnyl'
            },
            'Coverage': {
                'name': 'size',
                'zmax': {
                    'feasible': BIN_POP_SIZE,
                    'infeasible': BIN_POP_SIZE
                },
                'colorscale': 'Hot'
            }
        }
        self.hm_callback_props['method'] = {
            'Population': True,
            'Elite': False
        }