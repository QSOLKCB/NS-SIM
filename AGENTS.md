schema_version: "1.0.0"
document_type: "agent_contract"
project:
  name: "NS-SIM"
  repository: "QSOLKCB/NS-SIM"
  purpose: "deterministic_reproducible_fluid_dynamics_runtime"
  lifecycle: "private_pre_alpha"
authority:
  precedence:
    - "explicit_user_instruction"
    - "repository_contracts"
    - "task_scope"
    - "implementation_convenience"
  protected_claims:
    - "scientific_contract"
    - "determinism_contract"
    - "validation_contract"
    - "canonical_reference_semantics"
ai_documentation:
  machine_readable_only: true
  applies_to:
    - "AGENTS.md"
    - "docs/agents/**"
  content_formats:
    AGENTS.md: "yaml"
    allowed_extensions:
      - ".yaml"
      - ".yml"
      - ".json"
      - ".toml"
  forbidden_content_styles:
    - "freeform_agent_markdown"
    - "agent_narrative_prose_documents"
    - "agent_only_tables_for_human_reading"
    - "agent_instructions_embedded_only_in_comments"
  human_documentation_may_use_markdown: true
scientific_rules:
  required:
    - "declare_governing_equations"
    - "declare_discretization"
    - "declare_boundary_conditions"
    - "declare_initial_conditions"
    - "declare_timestep_policy"
    - "declare_precision"
    - "declare_solver_tolerances"
    - "declare_backend"
    - "emit_reproducibility_metadata"
    - "distinguish_reference_state_from_derived_views"
  prohibited_claims:
    - "numerical_simulation_is_exact_continuum_solution"
    - "project_solves_navier_stokes_millennium_problem"
    - "cross_gpu_bitwise_determinism_without_evidence"
    - "validated_without_defined_reference_and_tolerance"
    - "canonical_result_changed_by_visualization_or_sonification"
determinism:
  canonical_reference_backend: "cpu"
  classes:
    R0: "contract_reproducible"
    R1: "initial_state_reproducible"
    R2: "backend_local_bitwise_reproducible"
    R3: "cross_backend_numerically_reproducible"
    R4: "canonical_reference_reproducible"
  gpu_policy:
    require_backend_identity: true
    require_device_identity: true
    require_precision_identity: true
    require_tolerance_for_cross_backend_comparison: true
    forbid_implicit_bitwise_equivalence: true
change_control:
  before_modification:
    - "inspect_relevant_repository_files"
    - "identify_contracts_affected"
    - "preserve_unrelated_user_changes"
  canonical_changes_require:
    - "explicit_documentation_update"
    - "validation_update"
    - "regression_test_update"
    - "receipt_schema_impact_review"
  backend_changes_require:
    - "reference_comparison"
    - "determinism_classification"
    - "hardware_software_provenance"
  documentation_changes_require:
    - "links_remain_consistent"
    - "claims_remain_within_implemented_evidence"
validation:
  minimum_reference_cases:
    - "taylor_green_vortex"
    - "poiseuille_flow"
    - "lid_driven_cavity"
    - "cylinder_wake"
  required_diagnostics:
    - "finite_state"
    - "divergence_norm"
    - "solver_convergence"
    - "cfl_or_timestep_admissibility"
    - "energy_or_case_specific_budget"
  regression_policy: "small_canonical_cases_must_be_automatable"
security:
  secrets:
    commit: false
    log: false
    include_in_receipts: false
  remote_compute:
    treat_remote_hosts_as_untrusted: true
    require_explicit_artifact_transfer: true
    require_hash_verification: true
    prohibit_credential_embedding_in_experiment_files: true
workflow:
  default_branch: "main"
  change_style: "pull_request"
  branch_policy: "scoped_branch"
  commit_policy: "focused_commits"
  required_checks_when_available:
    - "tests"
    - "validation"
    - "schema_validation"
    - "documentation_consistency"
release:
  stable_release_requires:
    - "tagged_source_revision"
    - "documented_environment"
    - "validation_report"
    - "known_limitations"
    - "reproducibility_instructions"
    - "license"
    - "changelog"
agent_failure_policy:
  on_ambiguity: "prefer_narrow_conservative_change"
  on_missing_evidence: "state_unverified_do_not_upgrade_claim"
  on_failed_validation: "do_not_describe_change_as_validated"
  on_contract_conflict: "stop_contract_mutation_and_surface_conflict"
