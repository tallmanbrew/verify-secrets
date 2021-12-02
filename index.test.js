const verify_secrets = require('./verify-secrets');
const core = require('@actions/core');

jest.mock("@actions/core");

test('all secrets available - secret name json', async () => {
  // Arrange
  var secretNamesJson = `
  [
    "SECRET_1",
    "SECRET_2"
  ]
  `;

  // Act
  await verify_secrets(null, secretNamesJson);

  // Assert
  expect(core.setFailed).not.toHaveBeenCalled();

  jest.clearAllMocks();
});

test('all secrets available - full secret json', async () => {
  // Arrange
  var secretsObj = new Object();
  secretsObj.SECRET_1 = "SECRET_1_VALUE";
  secretsObj.SECRET_2 = "SECRET_2_VALUE";
  var secretsJson = JSON.stringify(secretsObj);

  // Act
  await verify_secrets(secretsJson,null);

  // Assert
  expect(core.setFailed).not.toHaveBeenCalled();

  jest.clearAllMocks();
});


test('missing secret - secret name json', async () => {
  // Arrange
  var secretNamesJson = `
  [
    "SECRET_1"
  ]
  `;

  // Act
  await verify_secrets(null, secretNamesJson);

  // Assert
  expect(core.setFailed).toHaveBeenCalled();
  expect(core.error).toHaveBeenCalledWith('Secret "SECRET_2" is not defined');

  jest.clearAllMocks();
});

test('missing secret - full secret json', async () => {
  // Arrange
  var secretsObj = new Object();
  secretsObj.SECRET_1 = "SECRET_1_VALUE";
  var secretsJson = JSON.stringify(secretsObj);

  // Act
  await verify_secrets(secretsJson, null);

  // Assert
  expect(core.setFailed).toHaveBeenCalled();
  expect(core.error).toHaveBeenCalledWith('Secret "SECRET_2" is not defined');

  jest.clearAllMocks();
});


test('neither input defined', async () => {
  // Arrange

  // Act
  await verify_secrets(null, null);

  // Assert
  expect(core.setFailed).toHaveBeenCalledWith("You must provide either the 'secrets' or 'secret_names' inputs");

  jest.clearAllMocks();
});

test('both inputs defined', async () => {
  // Arrange
  var secretsObj = new Object();
  secretsObj.SECRET_1 = "SECRET_1_VALUE";
  secretsObj.SECRET_2 = "SECRET_2_VALUE";
  var secretsJson = JSON.stringify(secretsObj);

  var secretNamesJson = `
  [
    "SECRET_1",
    "SECRET_2"
  ]
  `;

  // Act
  await verify_secrets(secretsJson, secretNamesJson);

  // Assert
  expect(core.setFailed).toHaveBeenCalledWith("You cannot provide both the 'secrets' and 'secret_names' inputs");

  jest.clearAllMocks();
});
