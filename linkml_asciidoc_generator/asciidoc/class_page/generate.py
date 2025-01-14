from linkml_asciidoc_generator.linkml.model import (
    LinkMLClass,
    LinkMLClassName,
    LinkMLElement,
    LinkMLSlot,
    LinkMLSlotOwner,
    LinkMLSchema,
    LinkMLPrimitive,
)
from linkml_asciidoc_generator.config import Config
from linkml_asciidoc_generator.asciidoc.class_page.model import (
    ClassPage,
    Class,
    CIMStandard,
    Relation,
    Attribute,
    RelationsDiagram,
    PositiveInt,
    SkosVerb,
    SkosMapping,
)
from linkml_asciidoc_generator.asciidoc.class_page.standard_mapping import (
    CLASSES_IN_STANDARD,
)
from linkml_asciidoc_generator.linkml.query import (
    get_ancestors,
    get_relations,
    get_attributes,
)

CIM_DATA_TYPES = [
    "cim:ActivePower",
    "cim:ActivePowerChangeRate",
    "cim:ActivePowerPerCurrentFlow",
    "cim:ActivePowerPerFrequency",
    "cim:Admittance",
    "cim:AngleDegrees",
    "cim:AngleRadians",
    "cim:ApparentPower",
    "cim:Area",
    "cim:Bearing",
    "cim:Capacitance",
    "cim:CapacitancePerLength",
    "cim:Classification",
    "cim:Conductance",
    "cim:ConductancePerLength",
    "cim:CostPerEnergyUnit",
    "cim:CostPerHeatUnit",
    "cim:CostPerVolume",
    "cim:CostRate",
    "cim:CurrentFlow",
    "cim:Damping",
    "cim:Displacement",
    "cim:Emission",
    "cim:Frequency",
    "cim:HeatRate",
    "cim:Hours",
    "cim:Impedance",
    "cim:Inductance",
    "cim:InductancePerLength",
    "cim:KiloActivePower",
    "cim:Length",
    "cim:MagneticField",
    "cim:Mass",
    "cim:Minutes",
    "cim:Money",
    "cim:ParticulateDensity",
    "cim:PerCent",
    "cim:Pressure",
    "cim:PU",
    "cim:Reactance",
    "cim:ReactancePerLength",
    "cim:ReactivePower",
    "cim:RealEnergy",
    "cim:Resistance",
    "cim:ResistancePerLength",
    "cim:RotationSpeed",
    "cim:Seconds",
    "cim:Speed",
    "cim:Susceptance",
    "cim:SusceptancePerLength",
    "cim:Temperature",
    "cim:Voltage",
    "cim:VoltagePerReactivePower",
    "cim:Volume",
    "cim:VolumeFlowRate",
    "cim:WaterLevel",
]


def is_cim_data_type(class_: LinkMLClass):
    return class_.class_uri in CIM_DATA_TYPES


def _get_min_cardinality(slot: LinkMLSlot) -> int:
    return int(slot.required)


def _get_max_cardinality(slot: LinkMLSlot) -> PositiveInt | None:
    match slot.multivalued:
        case False:
            return 1
        case True:
            return None


def _generate_data_type(slot_range: LinkMLClassName) -> LinkMLPrimitive | None:
    # TODO: Implement other types than primitive ones.

    for enum_val in dict(LinkMLPrimitive.__members__).values():
        if enum_val.value == slot_range:
            return enum_val

    return None


def _generate_attribute(slot_owner: LinkMLSlotOwner, slot: LinkMLSlot) -> Attribute:
    return Attribute(
        name=slot._meta["name"],
        data_type=_generate_data_type(slot.range),
        inherited_from=slot_owner,
        description=slot.description,
        uri=slot.slot_uri,
        min_cardinality=_get_min_cardinality(slot),
        max_cardinality=_get_max_cardinality(slot),
        skos_mappings=_get_skos_mappings(slot),
    )


def _generate_relation(
    slot_owner: LinkMLSlotOwner, slot: LinkMLSlot, schema: LinkMLSchema, config: Config
) -> Relation:
    target_class = schema.classes[slot.range]
    return Relation(
        name=slot._meta["name"],
        destination_class=Class(
            name=target_class._meta["name"],
            is_abstract=bool(target_class.abstract),
            is_mixin=bool(target_class.mixin),
            is_cim_data_type=is_cim_data_type(target_class),
            description=target_class.description,
            uri=target_class.class_uri,
            ancestors=[],
            attributes=[],
            relations=[],  # No need for these, and can cause recursion errors such as with `Terminal.topologicalNodes <-> TopologicalNode.terminal``
            prefixes=schema.prefixes,
            standard=_get_standard(target_class),
        ),
        inherited_from=slot_owner,
        description=slot.description,
        uri=slot.slot_uri,
        min_cardinality=_get_min_cardinality(slot),
        max_cardinality=_get_max_cardinality(slot),
        skos_mappings=_get_skos_mappings(slot),
    )


def _get_standard(class_: LinkMLClass) -> CIMStandard | None:
    # TODO: This is a temporary semi-hardcoded solution.

    standard = CIMStandard.IEC61970

    for standard, classes in CLASSES_IN_STANDARD.items():
        if class_.class_uri in classes:
            return standard
    return None


def _get_skos_mappings(element: LinkMLElement) -> SkosMapping:
    mappings = {}

    if element.exact_mappings:
        mappings[SkosVerb.EXACT_MATCH] = element.exact_mappings
    if element.close_mappings:
        mappings[SkosVerb.CLOSE_MATCH] = element.close_mappings
    if element.narrow_mappings:
        mappings[SkosVerb.NARROW_MATCH] = element.narrow_mappings
    if element.broad_mappings:
        mappings[SkosVerb.BROAD_MATCH] = element.broad_mappings
    if element.mappings:
        mappings[SkosVerb.MAPPING_RELATION] = element.mappings

    return mappings


def generate_class(class_: LinkMLClass, schema: LinkMLSchema, config: Config) -> Class:
    _class_ = Class(
        name=class_._meta["name"],
        is_abstract=bool(class_.abstract),
        is_mixin=bool(class_.mixin),
        is_root=bool(class_.tree_root),
        is_cim_data_type=is_cim_data_type(class_),
        description=class_.description,
        uri=class_.class_uri,
        ancestors=[c._meta["name"] for c in get_ancestors(class_, schema)],
        attributes=[
            _generate_attribute(a[0] if a[0] != class_._meta["name"] else None, a[1])
            for a in get_attributes(class_, schema)
        ],
        relations=[
            _generate_relation(
                r[0] if r[0] != class_._meta["name"] else None, r[1], schema, config
            )
            for r in get_relations(class_, schema)
        ],
        prefixes=schema.prefixes,
        standard=_get_standard(class_),
        skos_mappings=_get_skos_mappings(class_),
    )

    return _class_


def generate_class_page(
    class_: LinkMLClass, schema: LinkMLSchema, config: Config
) -> ClassPage:
    _class_ = generate_class(class_, schema, config)

    if config["diagrams"]["relations"]:
        relations_diagram = RelationsDiagram(
            name=f"{_class_.name}_relations",
            template=config["templates"]["class_page_relations_diagram"],
            class_=_class_,
        )
    else:
        relations_diagram = None

    page = ClassPage(
        name=_class_.name,
        template=config["templates"]["class_page"],
        title=class_.title or _class_.name,
        class_=_class_,
        relations_diagram=relations_diagram,
    )

    return page
