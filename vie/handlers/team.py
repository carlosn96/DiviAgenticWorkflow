from typing import Any, Dict, List
from vie.building import RowBuilder
from vie.handlers._registry import register


@register("team")
class TeamSectionHandler:
    section_type = "team"

    def build(self, sec_def: Dict, index: int, director: Any,
              module_builder: Any, decorator: Any,
              block: Dict, props: Dict) -> List[Dict]:
        members = sec_def.get("members", [])
        if members:
            modules = []
            for m in members[:4]:
                img = m.get("image", "")
                name = m.get("name", "")
                role = m.get("role", "")
                bio = m.get("text", m.get("bio", ""))
                mod = {"type": "divi/team-member", "module": "divi/team-member"}
                fields = {}
                if name:
                    fields["name"] = name
                if role:
                    fields["position"] = role
                if bio:
                    fields["content"] = bio
                if img:
                    fields["image"] = img
                if fields:
                    mod.update(fields)
                modules.append(mod)
            return [RowBuilder.grid_row(modules, max_cols=4)]
        return []
