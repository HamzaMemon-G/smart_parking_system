"""Parking Slot Management"""

from typing import List, Dict, Optional
from database.db_manager import get_db_manager


class ParkingSlotManager:
    
    def __init__(self):
        self.db = get_db_manager()
    
    def initialize_parking_structure(self, 
                                    floors: int = 3,
                                    sections_per_floor: int = 3,
                                    slots_per_section: int = 10) -> tuple[bool, str]:
        sections = ['A', 'B', 'C', 'D', 'E', 'F']
        slot_types = ['regular', 'covered', 'ev_charging']
        
        base_prices = {
            'car': 20.0,
            'bike': 10.0,
            'truck': 30.0
        }
        
        created_count = 0
        
        for floor in range(1, floors + 1):
            for sec_idx in range(sections_per_floor):
                section = sections[sec_idx]
                
                for slot_num in range(1, slots_per_section + 1):
                    if slot_num <= 6:
                        v_type = 'car'
                    elif slot_num <= 8:
                        v_type = 'bike'
                    else:
                        v_type = 'truck'
                    
                    if slot_num == 2:
                        s_type = 'covered'
                    elif slot_num == 3:
                        s_type = 'ev_charging'
                    else:
                        s_type = 'regular'
                    
                    slot_number = f"{section}-{floor}{slot_num:02d}"
                    base_price = base_prices[v_type]
                    
                    if s_type == 'covered':
                        base_price *= 1.2
                    elif s_type == 'ev_charging':
                        base_price *= 1.5
                    
                    slot_id = self.db.create_parking_slot(
                        slot_number, floor, section, v_type, base_price, s_type
                    )
                    
                    if slot_id:
                        created_count += 1
        
        return True, f"Parking structure initialized: {created_count} slots created"
    
    def get_all_slots(self) -> List[Dict]:
        slots = self.db.get_all_slots()
        return [dict(slot) for slot in slots]
    
    def get_available_slots(self, vehicle_type: str = None, 
                           floor: int = None, 
                           slot_type: str = None) -> List[Dict]:
        slots = self.db.get_available_slots(vehicle_type)
        slot_list = [dict(slot) for slot in slots]
        
        if floor is not None:
            slot_list = [s for s in slot_list if int(s['floor']) == int(floor)]
        
        if slot_type:
            slot_list = [s for s in slot_list if s['slot_type'] == slot_type]
        
        return slot_list
    
    def get_slot_by_id(self, slot_id: int) -> Optional[Dict]:
        slot = self.db.get_slot_by_id(slot_id)
        return dict(slot) if slot else None
    
    def get_slot_statistics(self) -> Dict:
        stats = self.db.get_slot_statistics()
        if not stats or not isinstance(stats, dict):
            stats = {'total': 0, 'available': 0, 'occupied': 0, 'reserved': 0, 'maintenance': 0}
        
        total = stats.get('total', 0)
        if total > 0:
            occupied = stats.get('occupied', 0)
            stats['occupancy_percentage'] = (occupied / total) * 100
        else:
            stats['occupancy_percentage'] = 0.0
        
        return stats
    
    def update_slot_status(self, slot_id: int, status: str) -> tuple[bool, str]:
        """Update slot status (available, occupied, reserved, maintenance)"""
        valid_statuses = ['available', 'occupied', 'reserved', 'maintenance']
        
        if status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        success = self.db.update_slot_status(slot_id, status)
        if success:
            return True, f"Slot status updated to {status}"
        return False, "Failed to update slot status"
    
    def get_slots_by_floor(self, floor: int) -> List[Dict]:
        """Get all slots on a specific floor"""
        all_slots = self.get_all_slots()
        return [slot for slot in all_slots if slot['floor'] == floor]
    
    def get_slots_by_section(self, section: str) -> List[Dict]:
        """Get all slots in a section"""
        all_slots = self.get_all_slots()
        return [slot for slot in all_slots if slot['floor'] == floor]
    
    def get_slots_by_section(self, section: str) -> List[Dict]:
        all_slots = self.get_all_slots()
        return [slot for slot in all_slots if slot['section'] == section]
    
    def recommend_best_slot(self, vehicle_type: str, 
                           preference: str = None) -> Optional[Dict]:
        available = self.get_available_slots(vehicle_type)
        if not available:
            return None
        
        if preference == 'covered':
            covered = [s for s in available if s['slot_type'] == 'covered']
            if covered:
                return covered[0]
        
        elif preference == 'ev_charging':
            ev = [s for s in available if s['slot_type'] == 'ev_charging']
            if ev:
                return ev[0]
        
        elif preference == 'cheapest':
            return min(available, key=lambda x: x['base_price_per_hour'])
        
        return min(available, key=lambda x: (x['floor'], x['section']))
    
    def get_floor_occupancy(self) -> Dict[int, Dict]:
        all_slots = self.get_all_slots()
        floor_stats = {}
        
        for slot in all_slots:
            floor = slot['floor']
            if floor not in floor_stats:
                floor_stats[floor] = {
                    'total': 0,
                    'available': 0,
                    'occupied': 0,
                    'reserved': 0,
                    'maintenance': 0
                }
            
            floor_stats[floor]['total'] += 1
            status = slot['status']
            if status in floor_stats[floor]:
                floor_stats[floor][status] += 1
        
        return floor_stats
    
    def search_slots(self, search_term: str) -> List[Dict]:
        all_slots = self.get_all_slots()
        search_term = search_term.upper()
        return [
            slot for slot in all_slots 
            if search_term in slot['slot_number'].upper() or 
               search_term in slot['section'].upper()
        ]
