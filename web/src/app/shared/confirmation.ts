import { AfterViewInit, Component, ElementRef, output, viewChild } from '@angular/core';
@Component({
  selector: 'app-confirmation',
  template: `<dialog #dialog class="dialog" (cancel)="cancelled.emit()">
    <h2>Émettre ce justificatif ?</h2>
    <p>
      Le serveur vérifiera la signature et enregistrera l’attestation comme émise si elle est
      valide.
    </p>
    <div class="actions">
      <button class="button secondary" autofocus (click)="cancelled.emit()">Annuler</button
      ><button class="button" (click)="confirmed.emit()">Confirmer l’émission</button>
    </div>
  </dialog>`,
})
export class Confirmation implements AfterViewInit {
  cancelled = output<void>();
  confirmed = output<void>();
  private dialog = viewChild.required<ElementRef<HTMLDialogElement>>('dialog');
  ngAfterViewInit() {
    this.dialog().nativeElement.showModal();
  }
}
