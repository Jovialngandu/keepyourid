import { Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
@Component({ imports: [RouterLink], templateUrl: './info.html' })
export class Info {
  page = inject(ActivatedRoute).snapshot.data as {
    label: string;
    title: string;
    description: string;
    items: { title: string; text: string }[];
  };
}
