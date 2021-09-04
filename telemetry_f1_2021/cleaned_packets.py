"""
The hard work for this file was taken from here:
https://forums.codemasters.com/topic/
80231-f1-2021-udp-specification/?do=findComment&comment=624274

"""

import ctypes
import json

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def to_json(*args, **kwargs):
    kwargs.setdefault("indent", 2)

    kwargs["sort_keys"] = True
    kwargs["ensure_ascii"] = False
    kwargs["separators"] = (",", ": ")

    return json.dumps(*args, **kwargs)


class PacketMixin(object):
    """A base set of helper methods for ctypes based packets"""

    def get_value(self, field):
        """Returns the field's value and formats the types value"""
        return self._format_type(getattr(self, field))

    def pack(self):
        """Packs the current data structure into a compressed binary

        Returns:
            (bytes):
                - The packed binary

        """
        return bytes(self)

    @classmethod
    def size(cls):
        return ctypes.sizeof(cls)

    @classmethod
    def unpack(cls, buffer):
        """Attempts to unpack the binary structure into a python structure

        Args:
            buffer (bytes):
                - The encoded buffer to decode

        """
        return cls.from_buffer_copy(buffer)

    def to_dict(self):
        """Returns a ``dict`` with key-values derived from _fields_"""
        return {k: self.get_value(k) for k, _ in self._fields_}

    def to_json(self):
        """Returns a ``str`` of sorted JSON derived from _fields_"""
        return to_json(self.to_dict())

    def _format_type(self, value):
        """A type helper to format values"""
        class_name = type(value).__name__

        if class_name == "float":
            return round(value, 3)

        if class_name == "bytes":
            return value.decode()

        if isinstance(value, ctypes.Array):
            return _format_array_type(value)

        if hasattr(value, "to_dict"):
            return value.to_dict()

        return value


def _format_array_type(value):
    results = []

    for item in value:
        if isinstance(item, Packet):
            results.append(item.to_dict())
        else:
            results.append(item)

    return results


class Packet(ctypes.LittleEndianStructure, PacketMixin):
    """The base packet class for API version 2021"""

    _pack_ = 1

    def __repr__(self):
        return self.to_json()


class PacketHeader(Packet):
    _fields_ = [
        ("packet_format", ctypes.c_uint16),  # 2021
        ("game_major_version", ctypes.c_uint8),  # Game major version - "X.00"
        ("game_minor_version", ctypes.c_uint8),  # Game minor version - "1.XX"
        ("packet_version", ctypes.c_uint8),
        # Version of this packet type, all start from 1
        ("packet_id", ctypes.c_uint8),  # Identifier for the packet type, see below
        ("session_uid", ctypes.c_uint64),  # Unique identifier for the session
        ("session_time", ctypes.c_float),  # Session timestamp
        ("frame_identifier", ctypes.c_uint32),
        # Identifier for the frame the data was retrieved on
        ("player_car_index", ctypes.c_uint8),  # Index of player's car in the array
        ("secondary_player_car_index", ctypes.c_uint8),
        # Index of secondary player's car in the array (splitscreen)
        # 255 if no second player
    ]


class CarMotionData(Packet):
    _fields_ = [
        ("world_position_x", ctypes.c_float),  # World space X position
        ("world_position_y", ctypes.c_float),  # World space Y position
        ("world_position_z", ctypes.c_float),  # World space Z position
        ("world_velocity_x", ctypes.c_float),  # Velocity in world space X
        ("world_velocity_y", ctypes.c_float),  # Velocity in world space Y
        ("world_velocity_z", ctypes.c_float),  # Velocity in world space Z
        ("world_forward_dir_x", ctypes.c_int16),  # World space forward X direction
        # (normalised)a
        ("world_forward_dir_y", ctypes.c_int16),
        # World space forward Y direction (normalised)
        ("world_forward_dir_z", ctypes.c_int16),
        # World space forward Z direction (normalised)
        ("world_right_dir_x", ctypes.c_int16),
        # World space right X direction (normalised)
        ("world_right_dir_y", ctypes.c_int16),
        # World space right Y direction (normalised)
        ("world_right_dir_z", ctypes.c_int16),
        # World space right Z direction (normalised)
        ("g_force_lateral", ctypes.c_float),  # Lateral G-Force component
        ("g_force_longitudinal", ctypes.c_float),  # Longitudinal G-Force component
        ("g_force_vertical", ctypes.c_float),  # Vertical G-Force component
        ("yaw", ctypes.c_float),  # Yaw angle in radians
        ("pitch", ctypes.c_float),  # Pitch angle in radians
        ("roll", ctypes.c_float),  # Roll angle in radians
    ]


class PacketMotionData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("car_motion_data", CarMotionData * 22),  # Data for all cars on track
        # Extra player car ONLY data
        ("suspension_position", ctypes.c_float * 4),
        # Note: All wheel arrays have the following order:
        ("suspension_velocity", ctypes.c_float * 4),  # RL, RR, FL, FR
        ("suspension_acceleration", ctypes.c_float * 4),  # RL, RR, FL, FR
        ("wheel_speed", ctypes.c_float * 4),  # Speed of each wheel
        ("wheel_slip", ctypes.c_float * 4),  # Slip ratio for each wheel
        ("local_velocity_x", ctypes.c_float),  # Velocity in local space
        ("local_velocity_y", ctypes.c_float),  # Velocity in local space
        ("local_velocity_z", ctypes.c_float),  # Velocity in local space
        ("angular_velocity_x", ctypes.c_float),  # Angular velocity x-component
        ("angular_velocity_y", ctypes.c_float),  # Angular velocity y-component
        ("angular_velocity_z", ctypes.c_float),  # Angular velocity z-component
        ("angular_acceleration_x", ctypes.c_float),  # Angular velocity x-component
        ("angular_acceleration_y", ctypes.c_float),  # Angular velocity y-component
        ("angular_acceleration_z", ctypes.c_float),  # Angular velocity z-component
        ("front_wheels_angle", ctypes.c_float),
        # Current front wheels angle in radians
    ]


class MarshalZone(Packet):
    _fields_ = [
        ("zone_start", ctypes.c_float),
        # Fraction (0..1) of way through the lap the marshal zone starts
        ("zone_flag", ctypes.c_int8),
        # -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow, 4 = red
    ]


class WeatherForecastSample(Packet):
    _fields_ = [
        ("session_type", ctypes.c_uint8),
        # 0 = unknown, 1 = P1, 2 = P2, 3 = P3, 4 = Short P, 5 = Q1
        # 6 = Q2, 7 = Q3, 8 = Short Q, 9 = OSQ, 10 = R, 11 = R2
        # 12 = Time Trial
        ("time_offset", ctypes.c_uint8),  # Time in minutes the forecast is for
        ("weather", ctypes.c_uint8),
        # Weather - 0 = clear, 1 = light cloud, 2 = overcast
        # 3 = light rain, 4 = heavy rain, 5 = storm
        ("track_temperature", ctypes.c_int8),  # Track temp. in degrees Celsius
        ("track_temperature_change", ctypes.c_int8),
        # Track temp. change – 0 = up, 1 = down, 2 = no change
        ("air_temperature", ctypes.c_int8),  # Air temp. in degrees celsius
        ("air_temperature_change", ctypes.c_int8),
        # Air temp. change – 0 = up, 1 = down, 2 = no change
        ("rain_percentage", ctypes.c_uint8),  # Rain percentage (0-100)
    ]


class PacketSessionData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("weather", ctypes.c_uint8),
        # Weather - 0 = clear, 1 = light cloud, 2 = overcast
        # 3 = light rain, 4 = heavy rain, 5 = storm
        ("track_temperature", ctypes.c_int8),  # Track temp. in degrees celsius
        ("air_temperature", ctypes.c_int8),  # Air temp. in degrees celsius
        ("total_laps", ctypes.c_uint8),  # Total number of laps in this race
        ("track_length", ctypes.c_uint16),  # Track length in metres
        ("session_type", ctypes.c_uint8),
        # 0 = unknown, 1 = P1, 2 = P2, 3 = P3, 4 = Short P
        # 5 = Q1, 6 = Q2, 7 = Q3, 8 = Short Q, 9 = OSQ
        # 10 = R, 11 = R2, 12 = R3, 13 = Time Trial
        ("track_id", ctypes.c_int8),  # -1 for unknown, 0-21 for tracks, see appendix
        ("formula", ctypes.c_uint8),
        # Formula, 0 = F1 Modern, 1 = F1 Classic, 2 = F2,
        # 3 = F1 Generic
        ("session_time_left", ctypes.c_uint16),  # Time left in session in seconds
        ("session_duration", ctypes.c_uint16),  # Session duration in seconds
        ("pit_speed_limit", ctypes.c_uint8),  # Pit speed limit in kilometres per hour
        ("game_paused", ctypes.c_uint8),  # Whether the game is paused
        ("is_spectating", ctypes.c_uint8),  # Whether the player is spectating
        ("spectator_car_index", ctypes.c_uint8),  # Index of the car being spectated
        ("sli_pro_native_support", ctypes.c_uint8),
        # SLI Pro support, 0 = inactive, 1 = active
        ("num_marshal_zones", ctypes.c_uint8),  # Number of marshal zones to follow
        ("marshal_zones", MarshalZone * 21),  # List of marshal zones – max 21
        ("safety_car_status", ctypes.c_uint8),  # 0 = no safety car, 1 = full
        # 2 = virtual, 3 = formation lap
        ("network_game", ctypes.c_uint8),  # 0 = offline, 1 = online
        ("num_weather_forecast_samples", ctypes.c_uint8),
        # Number of weather samples to follow
        ("weather_forecast_samples", WeatherForecastSample * 56),
        # Array of weather forecast samples
        ("forecast_accuracy", ctypes.c_uint8),  # 0 = Perfect, 1 = Approximate
        ("ai_difficulty", ctypes.c_uint8),  # AI Difficulty rating – 0-110
        ("season_link_identifier", ctypes.c_uint32),
        # Identifier for season - persists across saves
        ("weekend_link_identifier", ctypes.c_uint32),
        # Identifier for weekend - persists across saves
        ("session_link_identifier", ctypes.c_uint32),
        # Identifier for session - persists across saves
        ("pit_stop_window_ideal_lap", ctypes.c_uint8),
        # Ideal lap to pit on for current strategy (player)
        ("pit_stop_window_latest_lap", ctypes.c_uint8),
        # Latest lap to pit on for current strategy (player)
        ("pit_stop_rejoin_position", ctypes.c_uint8),
        # Predicted position to rejoin at (player)
        ("steering_assist", ctypes.c_uint8),  # 0 = off, 1 = on
        ("braking_assist", ctypes.c_uint8),  # 0 = off, 1 = low, 2 = medium, 3 = high
        ("gearbox_assist", ctypes.c_uint8),
        # 1 = manual, 2 = manual & suggested gear, 3 = auto
        ("pit_assist", ctypes.c_uint8),  # 0 = off, 1 = on
        ("pit_release_assist", ctypes.c_uint8),  # 0 = off, 1 = on
        ("ersassist", ctypes.c_uint8),  # 0 = off, 1 = on
        ("drsassist", ctypes.c_uint8),  # 0 = off, 1 = on
        ("dynamic_racing_line", ctypes.c_uint8),
        # 0 = off, 1 = corners only, 2 = full
        ("dynamic_racing_line_type", ctypes.c_uint8),  # 0 = 2D, 1 = 3D
    ]


class LapData(Packet):
    _fields_ = [
        ("last_lap_time_in_ms", ctypes.c_uint32),  # Last lap time in milliseconds
        ("current_lap_time_in_ms", ctypes.c_uint32),
        # Current time around the lap in milliseconds
        ("sector1_time_in_ms", ctypes.c_uint16),  # Sector 1 time in milliseconds
        ("sector2_time_in_ms", ctypes.c_uint16),  # Sector 2 time in milliseconds
        ("lap_distance", ctypes.c_float),
        # Distance vehicle is around current lap in metres – could
        # be negative if line hasn’t been crossed yet
        ("total_distance", ctypes.c_float),
        # Total distance travelled in session in metres – could
        # be negative if line hasn’t been crossed yet
        ("safety_car_delta", ctypes.c_float),  # Delta in seconds for safety car
        ("car_position", ctypes.c_uint8),  # Car race position
        ("current_lap_num", ctypes.c_uint8),  # Current lap number
        ("pit_status", ctypes.c_uint8),  # 0 = none, 1 = pitting, 2 = in pit area
        ("num_pit_stops", ctypes.c_uint8),  # Number of pit stops taken in this race
        ("sector", ctypes.c_uint8),  # 0 = sector1, 1 = sector2, 2 = sector3
        ("current_lap_invalid", ctypes.c_uint8),
        # Current lap invalid - 0 = valid, 1 = invalid
        ("penalties", ctypes.c_uint8),
        # Accumulated time penalties in seconds to be added
        ("warnings", ctypes.c_uint8),  # Accumulated number of warnings issued
        ("num_unserved_drive_through_pens", ctypes.c_uint8),
        # Num drive through pens left to serve
        ("num_unserved_stop_go_pens", ctypes.c_uint8),
        # Num stop go pens left to serve
        ("grid_position", ctypes.c_uint8),
        # Grid position the vehicle started the race in
        ("driver_status", ctypes.c_uint8),
        # Status of driver - 0 = in garage, 1 = flying lap
        # 2 = in lap, 3 = out lap, 4 = on track
        ("result_status", ctypes.c_uint8),
        # Result status - 0 = invalid, 1 = inactive, 2 = active
        # 3 = finished, 4 = didnotfinish, 5 = disqualified
        # 6 = not classified, 7 = retired
        ("pit_lane_timer_active", ctypes.c_uint8),
        # Pit lane timing, 0 = inactive, 1 = active
        ("pit_lane_time_in_lane_in_ms", ctypes.c_uint16),
        # If active, the current time spent in the pit lane in ms
        ("pit_stop_timer_in_ms", ctypes.c_uint16),
        # Time of the actual pit stop in ms
        ("pit_stop_should_serve_pen", ctypes.c_uint8),
        # Whether the car should serve a penalty at this stop
    ]


class PacketLapData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("lap_data", LapData * 22),  # Lap data for all cars on track
    ]


class FastestLap(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),  # Vehicle index of car achieving fastest lap
        ("lap_time", ctypes.c_float),  # Lap time is in seconds
    ]


class Retirement(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),  # Vehicle index of car retiring
    ]


class TeamMateInPits(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),  # Vehicle index of team mate
    ]


class RaceWinner(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),  # Vehicle index of the race winner
    ]


class Penalty(Packet):
    _fields_ = [
        ("penalty_type", ctypes.c_uint8),  # Penalty type – see Appendices
        ("infringement_type", ctypes.c_uint8),  # Infringement type – see Appendices
        ("vehicle_idx", ctypes.c_uint8),
        # Vehicle index of the car the penalty is applied to
        ("other_vehicle_idx", ctypes.c_uint8),
        # Vehicle index of the other car involved
        ("time", ctypes.c_uint8),
        # Time gained, or time spent doing action in seconds
        ("lap_num", ctypes.c_uint8),  # Lap the penalty occurred on
        ("places_gained", ctypes.c_uint8),  # Number of places gained by this
    ]


class SpeedTrap(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),
        # Vehicle index of the vehicle triggering speed trap
        ("speed", ctypes.c_float),  # Top speed achieved in kilometres per hour
        ("overall_fastest_in_session", ctypes.c_uint8),
        # Overall fastest speed in session = 1, otherwise 0
        ("driver_fastest_in_session", ctypes.c_uint8),
        # Fastest speed for driver in session = 1, otherwise 0
    ]


class StartLights(Packet):
    _fields_ = [
        ("num_lights", ctypes.c_uint8),  # Number of lights showing
    ]


class DriveThroughPenaltyServed(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),
        # Vehicle index of the vehicle serving drive through
    ]


class StopGoPenaltyServed(Packet):
    _fields_ = [
        ("vehicle_idx", ctypes.c_uint8),
        # Vehicle index of the vehicle serving stop go
    ]


class Flashback(Packet):
    _fields_ = [
        ("flashback_frame_identifier", ctypes.c_uint32),
        # Frame identifier flashed back to
        ("flashback_session_time", ctypes.c_float),  # Session time flashed back to
    ]


class Buttons(Packet):
    _fields_ = [
        ("button_status", ctypes.c_uint32),
        # Bit flags specifying which buttons are being pressed
        # currently - see appendices
    ]


class EventDataDetails(ctypes.Union, PacketMixin):
    _fields_ = [
        ("fastest_lap", FastestLap),
        ("retirement", Retirement),
        ("team_mate_in_pits", TeamMateInPits),
        ("race_winner", RaceWinner),
        ("penalty", Penalty),
        ("speed_trap", SpeedTrap),
        ("start_lights", StartLights),
        ("drive_through_penalty_served", DriveThroughPenaltyServed),
        ("stop_go_penalty_served", StopGoPenaltyServed),
        ("flashback", Flashback),
        ("buttons", Buttons),
    ]


class PacketEventData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("event_string_code", ctypes.c_uint8 * 4),  # Event string code, see below
        ("event_details", EventDataDetails),
        # Event details - should be interpreted differently
        # for each type
    ]


class ParticipantData(Packet):
    _fields_ = [
        ("ai_controlled", ctypes.c_uint8),
        # Whether the vehicle is AI (1) or Human (0) controlled
        ("driver_id", ctypes.c_uint8),
        # Driver id - see appendix, 255 if network human
        ("network_id", ctypes.c_uint8),
        # Network id – unique identifier for network players
        ("team_id", ctypes.c_uint8),  # Team id - see appendix
        ("my_team", ctypes.c_uint8),  # My team flag – 1 = My Team, 0 = otherwise
        ("race_number", ctypes.c_uint8),  # Race number of the car
        ("nationality", ctypes.c_uint8),  # Nationality of the driver
        ("name", ctypes.c_char * 48),
        # Name of participant in UTF-8 format – null terminated
        # Will be truncated with … (U+2026) if too long
        ("your_telemetry", ctypes.c_uint8),
        # The player's UDP setting, 0 = restricted, 1 = public
    ]


class PacketParticipantsData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("num_active_cars", ctypes.c_uint8),
        # Number of active cars in the data – should match number of
        # cars on HUD
        ("participants", ParticipantData * 22),
    ]


class CarSetupData(Packet):
    _fields_ = [
        ("front_wing", ctypes.c_uint8),  # Front wing aero
        ("rear_wing", ctypes.c_uint8),  # Rear wing aero
        ("on_throttle", ctypes.c_uint8),
        # Differential adjustment on throttle (percentage)
        ("off_throttle", ctypes.c_uint8),
        # Differential adjustment off throttle (percentage)
        ("front_camber", ctypes.c_float),  # Front camber angle (suspension geometry)
        ("rear_camber", ctypes.c_float),  # Rear camber angle (suspension geometry)
        ("front_toe", ctypes.c_float),  # Front toe angle (suspension geometry)
        ("rear_toe", ctypes.c_float),  # Rear toe angle (suspension geometry)
        ("front_suspension", ctypes.c_uint8),  # Front suspension
        ("rear_suspension", ctypes.c_uint8),  # Rear suspension
        ("front_anti_roll_bar", ctypes.c_uint8),  # Front anti-roll bar
        ("rear_anti_roll_bar", ctypes.c_uint8),  # Front anti-roll bar
        ("front_suspension_height", ctypes.c_uint8),  # Front ride height
        ("rear_suspension_height", ctypes.c_uint8),  # Rear ride height
        ("brake_pressure", ctypes.c_uint8),  # Brake pressure (percentage)
        ("brake_bias", ctypes.c_uint8),  # Brake bias (percentage)
        ("rear_left_tyre_pressure", ctypes.c_float),  # Rear left tyre pressure (PSI)
        ("rear_right_tyre_pressure", ctypes.c_float),
        # Rear right tyre pressure (PSI)
        ("front_left_tyre_pressure", ctypes.c_float),
        # Front left tyre pressure (PSI)
        ("front_right_tyre_pressure", ctypes.c_float),
        # Front right tyre pressure (PSI)
        ("ballast", ctypes.c_uint8),  # Ballast
        ("fuel_load", ctypes.c_float),  # Fuel load
    ]


class PacketCarSetupData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("car_setups", CarSetupData * 22),
    ]


class CarTelemetryData(Packet):
    _fields_ = [
        ("speed", ctypes.c_uint16),  # Speed of car in kilometres per hour
        ("throttle", ctypes.c_float),  # Amount of throttle applied (0.0 to 1.0)
        ("steer", ctypes.c_float),
        # Steering (-1.0 (full lock left) to 1.0 (full lock right))
        ("brake", ctypes.c_float),  # Amount of brake applied (0.0 to 1.0)
        ("clutch", ctypes.c_uint8),  # Amount of clutch applied (0 to 100)
        ("gear", ctypes.c_int8),  # Gear selected (1-8, N=0, R=-1)
        ("engine_rpm", ctypes.c_uint16),  # Engine RPM
        ("drs", ctypes.c_uint8),  # 0 = off, 1 = on
        ("rev_lights_percent", ctypes.c_uint8),  # Rev lights indicator (percentage)
        ("rev_lights_bit_value", ctypes.c_uint16),
        # Rev lights (bit 0 = leftmost LED, bit 14 = rightmost LED)
        ("brakes_temperature", ctypes.c_uint16 * 4),  # Brakes temperature (celsius)
        ("tyre_surface_temperature", ctypes.c_uint8 * 4),
        # tyre surface temperature (celsius)
        ("tyre_inner_temperature", ctypes.c_uint8 * 4),
        # tyre inner temperature (celsius)
        ("engine_temperature", ctypes.c_uint16),  # Engine temperature (celsius)
        ("tyre_pressure", ctypes.c_float * 4),  # tyre pressure (PSI)
        ("surface_type", ctypes.c_uint8 * 4),  # Driving surface, see appendices
    ]


class PacketCarTelemetryData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("car_telemetry_data", CarTelemetryData * 22),
        ("mfd_panel_index", ctypes.c_uint8),
        # Index of MFD panel open - 255 = MFD closed
        # Single player, race – 0 = Car setup, 1 = Pits
        # 2 = Damage, 3 =  Engine, 4 = Temperatures
        # May vary depending on game mode
        ("mfd_panel_index_secondary_player", ctypes.c_uint8),  # See above
        ("suggested_gear", ctypes.c_int8),  # Suggested gear for the player (1-8)
        # 0 if no gear suggested
    ]


class CarStatusData(Packet):
    _fields_ = [
        ("traction_control", ctypes.c_uint8),
        # Traction control - 0 = off, 1 = medium, 2 = full
        ("anti_lock_brakes", ctypes.c_uint8),  # 0 (off) - 1 (on)
        ("fuel_mix", ctypes.c_uint8),
        # Fuel mix - 0 = lean, 1 = standard, 2 = rich, 3 = max
        ("front_brake_bias", ctypes.c_uint8),  # Front brake bias (percentage)
        ("pit_limiter_status", ctypes.c_uint8),
        # Pit limiter status - 0 = off, 1 = on
        ("fuel_in_tank", ctypes.c_float),  # Current fuel mass
        ("fuel_capacity", ctypes.c_float),  # Fuel capacity
        ("fuel_remaining_laps", ctypes.c_float),
        # Fuel remaining in terms of laps (value on MFD)
        ("max_rpm", ctypes.c_uint16),  # Cars max RPM, point of rev limiter
        ("idle_rpm", ctypes.c_uint16),  # Cars idle RPM
        ("max_gears", ctypes.c_uint8),  # Maximum number of gears
        ("drs_allowed", ctypes.c_uint8),  # 0 = not allowed, 1 = allowed
        ("drs_activation_distance", ctypes.c_uint16),
        # 0 = DRS not available, non-zero - DRS will be available
        # in [X] metres
        ("actual_tyre_compound", ctypes.c_uint8),
        # F1 Modern - 16 = C5, 17 = C4, 18 = C3, 19 = C2, 20 = C1
        # 7 = inter, 8 = wet
        # F1 Classic - 9 = dry, 10 = wet
        # F2 – 11 = super soft, 12 = soft, 13 = medium, 14 = hard
        # 15 = wet
        ("visual_tyre_compound", ctypes.c_uint8),
        # F1 visual (can be different from actual compound)
        # 16 = soft, 17 = medium, 18 = hard, 7 = inter, 8 = wet
        # F1 Classic – same as above
        # F2 ‘19, 15 = wet, 19 – super soft, 20 = soft
        # 21 = medium , 22 = hard
        ("tyre_age_laps", ctypes.c_uint8),  # Age in laps of the current set of tyre
        ("vehicle_fia_flags", ctypes.c_int8),
        # -1 = invalid/unknown, 0 = none, 1 = green
        # 2 = blue, 3 = yellow, 4 = red
        ("ers_store_energy", ctypes.c_float),  # ERS energy store in Joules
        ("ers_deploy_mode", ctypes.c_uint8),
        # ERS deployment mode, 0 = none, 1 = medium
        # 2 = hotlap, 3 = overtake
        ("ers_harvested_this_lap_mguk", ctypes.c_float),
        # ERS energy harvested this lap by MGU-K
        ("ers_harvested_this_lap_mguh", ctypes.c_float),
        # ERS energy harvested this lap by MGU-H
        ("ers_deployed_this_lap", ctypes.c_float),  # ERS energy deployed this lap
        ("network_paused", ctypes.c_uint8),
        # Whether the car is paused in a network game
    ]


class PacketCarStatusData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("car_status_data", CarStatusData * 22),
    ]


class FinalClassificationData(Packet):
    _fields_ = [
        ("position", ctypes.c_uint8),  # Finishing position
        ("num_laps", ctypes.c_uint8),  # Number of laps completed
        ("grid_position", ctypes.c_uint8),  # Grid position of the car
        ("points", ctypes.c_uint8),  # Number of points scored
        ("num_pit_stops", ctypes.c_uint8),  # Number of pit stops made
        ("result_status", ctypes.c_uint8),
        # Result status - 0 = invalid, 1 = inactive, 2 = active
        # 3 = finished, 4 = didnotfinish, 5 = disqualified
        # 6 = not classified, 7 = retired
        # Best lap time of the session in milliseconds
        ("best_lap_time_in_ms", ctypes.c_uint32),
        # Total race time in seconds without penalties
        ("total_race_time", ctypes.c_double),
        ("penalties_time", ctypes.c_uint8),  # Total penalties accumulated in seconds
        # Number of penalties applied to this driver
        ("num_penalties", ctypes.c_uint8),
        ("num_tyre_stints", ctypes.c_uint8),  # Number of tyre stints up to maximum
        # Actual tyre used by this driver
        ("tyre_stints_actual", ctypes.c_uint8 * 8),
        # Visual tyre used by this driver
        ("tyre_stints_visual", ctypes.c_uint8 * 8),
    ]


class PacketFinalClassificationData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("num_cars", ctypes.c_uint8),  # Number of cars in the final classification
        ("classification_data", FinalClassificationData * 22),
    ]


class LobbyInfoData(Packet):
    _fields_ = [
        ("ai_controlled", ctypes.c_uint8),
        # Whether the vehicle is AI (1) or Human (0) controlled
        ("team_id", ctypes.c_uint8),
        # Team id - see appendix (255 if no team currently selected)
        ("nationality", ctypes.c_uint8),  # Nationality of the driver
        # Name of participant in UTF-8 format – null terminated
        ("name", ctypes.c_char * 48),
        # Will be truncated with ... (U+2026) if too long
        ("car_number", ctypes.c_uint8),  # Car number of the player
        ("ready_status", ctypes.c_uint8),  # 0 = not ready, 1 = ready, 2 = spectating
    ]


class PacketLobbyInfoData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        # Packet specific data
        ("num_players", ctypes.c_uint8),  # Number of players in the lobby data
        ("lobby_players", LobbyInfoData * 22),
    ]


class CarDamageData(Packet):
    _fields_ = [
        ("tyre_wear", ctypes.c_float * 4),  # Tyre wear (percentage)
        ("tyre_damage", ctypes.c_uint8 * 4),  # Tyre damage (percentage)
        ("brakes_damage", ctypes.c_uint8 * 4),  # Brakes damage (percentage)
        # Front left wing damage (percentage)
        ("front_left_wing_damage", ctypes.c_uint8),
        # Front right wing damage (percentage)
        ("front_right_wing_damage", ctypes.c_uint8),
        ("rear_wing_damage", ctypes.c_uint8),  # Rear wing damage (percentage)
        ("floor_damage", ctypes.c_uint8),  # Floor damage (percentage)
        ("diffuser_damage", ctypes.c_uint8),  # Diffuser damage (percentage)
        ("sidepod_damage", ctypes.c_uint8),  # Sidepod damage (percentage)
        ("drs_fault", ctypes.c_uint8),  # Indicator for DRS fault, 0 = OK, 1 = fault
        ("gear_box_damage", ctypes.c_uint8),  # Gear box damage (percentage)
        ("engine_damage", ctypes.c_uint8),  # Engine damage (percentage)
        ("engine_mguhwear", ctypes.c_uint8),  # Engine wear MGU-H (percentage)
        ("engine_eswear", ctypes.c_uint8),  # Engine wear ES (percentage)
        ("engine_cewear", ctypes.c_uint8),  # Engine wear CE (percentage)
        ("engine_icewear", ctypes.c_uint8),  # Engine wear ICE (percentage)
        ("engine_mgukwear", ctypes.c_uint8),  # Engine wear MGU-K (percentage)
        ("engine_tcwear", ctypes.c_uint8),  # Engine wear TC (percentage)
    ]


class PacketCarDamageData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("car_damage_data", CarDamageData * 22),
    ]


class LapHistoryData(Packet):
    _fields_ = [
        ("lap_time_in_ms", ctypes.c_uint32),  # Lap time in milliseconds
        ("sector1_time_in_ms", ctypes.c_uint16),  # Sector 1 time in milliseconds
        ("sector2_time_in_ms", ctypes.c_uint16),  # Sector 2 time in milliseconds
        ("sector3_time_in_ms", ctypes.c_uint16),  # Sector 3 time in milliseconds
        ("lap_valid_bit_flags", ctypes.c_uint8),
        # 0x01 bit set-lap valid,      0x02 bit set-sector 1 valid
        # 0x04 bit set-sector 2 valid, 0x08 bit set-sector 3 valid
    ]


class TyreStintHistoryData(Packet):
    _fields_ = [
        # Lap the tyre usage ends on (255 of current tyre)
        ("end_lap", ctypes.c_uint8),
        ("tyre_actual_compound", ctypes.c_uint8),  # Actual tyre used by this driver
        ("tyre_visual_compound", ctypes.c_uint8),  # Visual tyre used by this driver
    ]


class PacketSessionHistoryData(Packet):
    _fields_ = [
        ("header", PacketHeader),  # Header
        ("car_idx", ctypes.c_uint8),  # Index of the car this lap data relates to
        # Num laps in the data (including current partial lap)
        ("num_laps", ctypes.c_uint8),
        ("num_tyre_stints", ctypes.c_uint8),  # Number of tyre stints in the data
        # Lap the best lap time was achieved on
        ("best_lap_time_lap_num", ctypes.c_uint8),
        # Lap the best Sector 1 time was achieved on
        ("best_sector1_lap_num", ctypes.c_uint8),
        # Lap the best Sector 2 time was achieved on
        ("best_sector2_lap_num", ctypes.c_uint8),
        # Lap the best Sector 3 time was achieved on
        ("best_sector3_lap_num", ctypes.c_uint8),
        ("lap_history_data", LapHistoryData * 100),  # 100 laps of data max
        ("tyre_stints_history_data", TyreStintHistoryData * 8),
    ]


HEADER_FIELD_TO_PACKET_TYPE = {
    (2021, 1, 0): PacketMotionData,
    (2021, 1, 1): PacketSessionData,
    (2021, 1, 2): PacketLapData,
    (2021, 1, 3): PacketEventData,
    (2021, 1, 4): PacketParticipantsData,
    (2021, 1, 5): PacketCarSetupData,
    (2021, 1, 6): PacketCarTelemetryData,
    (2021, 1, 7): PacketCarStatusData,
    (2021, 1, 8): PacketFinalClassificationData,
    (2021, 1, 9): PacketLobbyInfoData,
    (2021, 1, 10): PacketCarDamageData,
    (2021, 1, 11): PacketSessionHistoryData,
}
