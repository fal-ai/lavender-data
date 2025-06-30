export const formatFloat = (value: number) => {
  if (value.toFixed(2).endsWith('00')) {
    return value.toFixed(0);
  }
  return value.toFixed(2);
};

export const formatNumber = (value: number) => {
  if (value < 1000) {
    return `${formatFloat(value)}`;
  } else if (value < 1000 * 1000) {
    return `${formatFloat(value / 1000)}k`;
  } else if (value < 1000 * 1000 * 1000) {
    return `${formatFloat(value / 1000 / 1000)}m`;
  } else if (value < 1000 * 1000 * 1000 * 1000) {
    return `${formatFloat(value / 1000 / 1000 / 1000)}g`;
  } else {
    return `${formatFloat(value / 1000 / 1000 / 1000 / 1000)}t`;
  }
};
