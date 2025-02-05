from dataclasses import dataclass
from linkml_asciidoc_generator.asciidoc import Page
from linkml_asciidoc_generator.asciidoc import ResourceName
from linkml_asciidoc_generator.asciidoc.class_page.model import Class
from linkml_asciidoc_generator.asciidoc.enumeration_page.model import Enumeration


@dataclass
class NavigationPage(Page):
    classes: dict[ResourceName, Class]
    enumerations: dict[ResourceName, Enumeration]
    cim_data_types: dict[ResourceName, Class]
