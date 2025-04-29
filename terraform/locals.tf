locals {
  common_tags = {
    Environment     = var.environment
    Project        = var.project
    Owner          = "team-noc@company.com"
    CostCenter     = "it-ops-123"
    ManagedBy      = "terraform"
    GitRepository  = "GIALaboratory/CloudOpsAI"
  }

  resource_tags = merge(local.common_tags, {
    AutoRemediate = "true"
  })
}
