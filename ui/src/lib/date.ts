export function utcToLocal(datestr: string) {
  return new Date(
    datestr + (datestr.endsWith('Z') ? '' : 'Z')
  ).toLocaleString();
}
