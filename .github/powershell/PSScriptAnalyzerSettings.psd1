@{
    Severity = @('Error', 'Warning')
    ExcludeRules = @(
        # Write-Host est volontaire pour les interfaces opérateur du dépôt.
        'PSAvoidUsingWriteHost',
        # PowerShell 7 utilise UTF-8 sans BOM par défaut ; le dépôt reste cross-platform.
        'PSUseBOMForUnicodeEncodedFile'
    )
}
