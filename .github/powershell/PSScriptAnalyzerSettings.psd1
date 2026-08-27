@{
    Severity = @('Error', 'Warning')
    ExcludeRules = @(
        # Le dépôt utilise Write-Host volontairement pour ses interfaces opérateur.
        'PSAvoidUsingWriteHost'
    )
}
