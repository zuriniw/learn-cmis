import random

# The App class handles the content of the applications that can be displayed on the user interface.
# It randomizes the information for each level of detail (lod) and provides a method to concatenate the first (lod + 1) entries from the info list.
class App: 
    def __init__(self, name, info):
        self.name = name 

        # Initialize info for each lod
        lods = []
        for entry in info: 
            lods.append(self.init_info(entry))

        self.info = lods

    def init_info_time(self, start, end):
        start_minutes = int(start[:len(start)-2]) * 60 + int(start[-2:])
        end_minutes = int(end[:len(end)-2]) * 60 + int(end[-2:])
        
        # Generate random minutes within the range
        random_minutes = random.randint(start_minutes, end_minutes)
        
        # Convert random minutes back to "hh:mm" format
        random_hour = random_minutes // 60
        random_minute = random_minutes % 60
        
        return f"{random_hour:02d}:{random_minute:02d}"

    def init_info(self, entry):
        entry_type = entry["type"]
        value = ""
        if entry_type == "int":
            value = random.randint(entry["min"], entry["max"])
        elif entry_type == "time":
            start = str(entry["min"]).zfill(4)
            end = str(entry["max"]).zfill(4)
            value = self.init_info_time(start, end)
        return entry["label"] + " " + str(value)

    def get_lod(self, lod=0):
        """
        Concatenates the first (lod + 1) entries from the info list.

        Args:
            lod (int): An integer representing the number of entries to concatenate (0-based).

        Returns:
            str: A string containing the concatenated info entries.

        Raises:
            ValueError: If lod is not a valid index for the info list.
        """
        if not isinstance(lod, int) or lod < 0 or lod >= len(self.info):
            raise ValueError("lod invalid.")
        
        return "\n".join(self.info[:lod + 1])