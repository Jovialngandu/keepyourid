import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { finalize } from 'rxjs';
import { ApiService } from '../../core/api.service';
@Component({ imports: [ReactiveFormsModule], templateUrl: './register.html' })
export class Register {
  private fb = inject(FormBuilder);
  private api = inject(ApiService);
  busy = signal(false);
  error = signal('');
  result = signal('');
  form = this.fb.nonNullable.group({
    legal_name: ['', [Validators.required, Validators.minLength(2), Validators.pattern(/.*\S.*/)]],
    registration_number: ['', [Validators.required, Validators.pattern(/.*\S.*/)]],
    email: ['', [Validators.required, Validators.email]],
    phone: [''],
  });
  submit() {
    this.form.markAllAsTouched();
    if (this.form.invalid || this.busy()) return;
    this.error.set('');
    this.busy.set(true);
    const v = this.form.getRawValue();
    this.api
      .register({
        ...v,
        legal_name: v.legal_name.trim(),
        registration_number: v.registration_number.trim(),
      })
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({ next: (r) => this.result.set(r.id), error: (e) => this.error.set(e.message) });
  }
}
