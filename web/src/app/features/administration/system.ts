import { Component, inject, signal } from '@angular/core';
import { finalize } from 'rxjs';
import { ApiService } from '../../core/api.service';
@Component({ templateUrl: './system.html' })
export class System {
  private api = inject(ApiService);
  busy = signal(false);
  status = signal('Pas encore contrôlé');
  check() {
    if (this.busy()) return;
    this.busy.set(true);
    this.api
      .health()
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({
        next: (r) =>
          this.status.set(
            r.status === 'ok' ? 'API joignable' : 'Réponse reçue : état non confirmé',
          ),
        error: (e) => this.status.set(e.message),
      });
  }
}
