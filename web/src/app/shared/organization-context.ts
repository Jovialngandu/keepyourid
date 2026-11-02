import { Component, inject, input, output } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { WorkspaceService } from '../core/workspace.service';
export const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
@Component({
  selector: 'app-organization-context',
  imports: [ReactiveFormsModule],
  templateUrl: './organization-context.html',
})
export class OrganizationContext {
  workspace = inject(WorkspaceService);
  locked = input(false);
  selected = output<string>();
  id = new FormControl(this.workspace.organizationId(), {
    nonNullable: true,
    validators: [Validators.required, Validators.pattern(UUID_PATTERN)],
  });
  select(event: Event) {
    event.preventDefault();
    this.id.markAsTouched();
    if (this.id.invalid || this.locked()) return;
    const id = this.id.value.trim();
    this.workspace.organizationId.set(id);
    this.selected.emit(id);
  }
}
