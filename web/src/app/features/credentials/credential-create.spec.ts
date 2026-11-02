import { parseSubject } from './credential-create';
describe('Attributs du credential', () => {
  it('accepte un objet non vide', () =>
    expect(parseSubject('{"degree":"Master"}')).toEqual({ degree: 'Master' }));
  it.each(['null', '[]', '{}', '"string"', '42', 'invalid'])('rejette %s', (value) =>
    expect(() => parseSubject(value)).toThrow(),
  );
});
