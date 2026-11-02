import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { WorkspaceService } from '../../core/workspace.service';
import { UUID_PATTERN } from '../../shared/organization-context';
export function parseSubject(value: string): Record<string, unknown> {
  const subject: unknown = JSON.parse(value);
  if (
    !subject ||
    typeof subject !== 'object' ||
    Array.isArray(subject) ||
    !Object.keys(subject).length
  )
    throw new Error('Les attributs doivent être un objet JSON non vide.');
  return subject as Record<string, unknown>;
}
@Component({ imports: [ReactiveFormsModule], templateUrl: './credential-create.html' })
export class CredentialCreate {
  private fb = inject(FormBuilder);
  private api = inject(ApiService);
  private workspace = inject(WorkspaceService);
  private router = inject(Router);
  busy = signal(false);
  error = signal('');
  form = this.fb.nonNullable.group({
    organization: [
      this.workspace.organizationId(),
      [Validators.required, Validators.pattern(UUID_PATTERN)],
    ],
    credential_type: [
      '',
      [Validators.required, Validators.minLength(2), Validators.pattern(/.*\S.*/)],
    ],
    subject: ['', [Validators.required]],
    valid_until: [''],
  });
  submit() {
    this.form.markAllAsTouched();
    if (this.form.invalid || this.busy()) return;
    this.error.set('');
    const v = this.form.getRawValue();
    let subject: Record<string, unknown>;
    let until: string | undefined;
    try {
      subject = parseSubject(v.subject);
      if (v.valid_until) {
        const date = new Date(v.valid_until);
        if (!Number.isFinite(date.getTime()) || date.getTime() <= Date.now())
          throw new Error('La date d’expiration doit être dans le futur.');
        until = date.toISOString();
      }
    } catch (e) {
      this.error.set(e instanceof Error ? e.message : 'Attributs JSON invalides.');
      return;
    }
    this.busy.set(true);
    this.api
      .create(v.organization, {
        credential_type: v.credential_type.trim(),
        subject,
        ...(until ? { valid_until: until } : {}),
      })
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({
        next: (c) => {
          this.workspace.organizationId.set(v.organization);
          this.router.navigate(['/issuer/credentials', c.id]);
        },
        error: (e) => this.error.set(e.message),
      });
  }
}
