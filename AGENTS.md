schema_version: "1.1.0"
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
    - "verification_contract"
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
    - "declare_forcing_representation_and_units"
    - "emit_reproducibility_metadata"
    - "distinguish_reference_state_from_derived_views"
    - "distinguish_numerical_verification_from_physical_validation"
  forcing_contract:
    canonical_symbol: "f"
    canonical_meaning: "specific_body_force_acceleration"
    dimensional_units: "L/T^2"
    force_density_symbol: "b"
    force_density_conversion: "f=b/rho"
    require_input_representation: true
    require_units_or_nondimensional_convention: true
  prohibited_claims:
    - "numerical_simulation_is_exact_continuum_solution"
    - "project_solves_navier_stokes_millennium_problem"
    - "cross_gpu_bitwise_determinism_without_evidence"
    - "physical_validation_from_verification_evidence_alone"
    - "validated_without_physical_reference_uncertainty_metric_and_acceptance_criterion"
    - "canonical_result_changed_by_visualization_or_sonification"
determinism:
  canonical_reference_backend: "cpu"
  classes:
    R0:
      name: "contract_reproducible"
      scope: "normalized_semantic_experiment_contract"
      execution_provenance_required: false
      required_evidence:
        - "schema_valid_normalized_contract"
        - "stable_contract_identity"
    R1:
      name: "initial_state_reproducible"
      scope: "canonical_cpu_initialization_environment"
      required_environment:
        - "backend_identity"
        - "precision_identity"
        - "software_or_container_identity"
        - "serialization_contract_identity"
      hardware_identity: "required_when_material"
      required_evidence:
        - "serialized_initial_state_identity"
        - "initial_state_hash"
    R2:
      name: "backend_local_bitwise_reproducible"
      scope: "declared_backend_device_software_environment"
      execution_provenance_required: true
    R3:
      name: "cross_backend_numerically_reproducible"
      scope: "declared_metric_and_tolerance"
      execution_provenance_required: true
    R4:
      name: "canonical_reference_reproducible"
      scope: "pinned_cpu_reference_environment"
      execution_provenance_required: true
      archival_reference_required: true
  gpu_policy:
    require_backend_identity: true
    require_device_identity: true
    require_precision_identity: true
    require_tolerance_for_cross_backend_comparison: true
    forbid_implicit_bitwise_equivalence: true
verification_validation:
  numerical_verification:
    question: "implementation_solves_declared_mathematical_and_discrete_problem_consistently"
    qualifying_evidence:
      - "analytic_solution_comparison"
      - "manufactured_solution_comparison"
      - "spatial_or_temporal_refinement"
      - "numerical_benchmark_comparison"
      - "solver_residual_and_constraint_checks"
      - "backend_reference_comparison"
  physical_validation:
    question: "model_represents_physical_system_adequately_for_stated_scope"
    positive_claim_requires:
      - "experimental_or_observational_reference"
      - "simulation_to_measurement_mapping"
      - "measurement_and_input_uncertainty"
      - "comparison_metric"
      - "acceptance_criterion"
      - "declared_scope_and_regime"
    default_without_qualifying_evidence: "not_claimed"
change_control:
  before_modification:
    - "inspect_relevant_repository_files"
    - "identify_contracts_affected"
    - "preserve_unrelated_user_changes"
  canonical_changes_require:
    - "explicit_documentation_update"
    - "numerical_verification_update"
    - "physical_validation_impact_review"
    - "regression_test_update"
    - "receipt_schema_impact_review"
  backend_changes_require:
    - "reference_comparison"
    - "determinism_classification"
    - "hardware_software_provenance"
  documentation_changes_require:
    - "links_remain_consistent"
    - "claims_remain_within_implemented_evidence"
verification:
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
validation:
  positive_claim_policy: "requires_qualifying_physical_evidence"
  no_physical_evidence_status: "not_claimed"
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
    - "numerical_verification"
    - "schema_validation"
    - "documentation_consistency"
release:
  stable_release_requires:
    - "tagged_source_revision"
    - "documented_environment"
    - "numerical_verification_report"
    - "explicit_validation_status"
    - "known_limitations"
    - "reproducibility_instructions"
    - "license"
    - "changelog"
  physical_validation_report_required_when: "validation_status_is_positive"
agent_failure_policy:
  on_ambiguity: "prefer_narrow_conservative_change"
  on_missing_evidence: "state_unverified_do_not_upgrade_claim"
  on_failed_verification: "do_not_describe_numerical_behavior_as_verified"
  on_failed_validation: "do_not_describe_model_as_physically_validated"
  on_contract_conflict: "stop_contract_mutation_and_surface_conflict"
