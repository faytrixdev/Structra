from enum import StrEnum


class KnowledgeType(StrEnum):
    RULE = "Rule"
    DEFINITION = "Definition"
    PROCEDURE = "Procedure"
    DECISION = "Decision"
    WORKFLOW = "Workflow"
    RESPONSIBILITY = "Responsibility"
    CONSTRAINT = "Constraint"
    EXCEPTION = "Exception"
    REQUIREMENT = "Requirement"
    RISK = "Risk"
    EVENT = "Event"
    METRIC = "Metric"
    KPI = "KPI"
    POLICY = "Policy"
    CONCEPT = "Concept"
    OBLIGATION = "Obligation"
    PROHIBITION = "Prohibition"


class RelationType(StrEnum):
    DEPENDS_ON = "depends_on"
    REQUIRES = "requires"
    REFERENCES = "references"
    EXTENDS = "extends"
    CONTRADICTS = "contradicts"
    CAUSES = "causes"
    BLOCKS = "blocks"
    EXCEPTION_OF = "exception_of"
    WORKFLOW_STEP = "workflow_step"
    PARENT = "parent"
    CHILD = "child"


class EntityType(StrEnum):
    ACTOR = "actor"
    ACTION = "action"
    OBJECT = "object"


class ConditionType(StrEnum):
    CONDITION = "condition"
    CONSTRAINT = "constraint"
    EXCEPTION = "exception"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    CLEANING = "cleaning"
    SEGMENTING = "segmenting"
    EXTRACTING_IDEAS = "extracting_ideas"
    CLASSIFYING = "classifying"
    EXTRACTING_ENTITIES = "extracting_entities"
    BUILDING_RELATIONS = "building_relations"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class MemberRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
