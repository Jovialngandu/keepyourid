import { Component } from '@angular/core';
@Component({ templateUrl: './verification.html' })
export class Verification {
  checks = [
    'Structure du justificatif',
    'Signature cryptographique',
    'Identité et clé de l’émetteur',
    'Dates de validité',
    'Statut de révocation',
    'Reconnaissance de l’émetteur',
  ];
}
