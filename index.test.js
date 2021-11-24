const verify_secrets = require('./verify-secrets');
const core = require('@actions/core');

jest.mock("@actions/core");

test('all secrets available', async () => {
  // Arrange
  var secretsObj = new Object();
  secretsObj.SECRET_1 = "SECRET_1_VALUE";
  secretsObj.SECRET_2 = "SECRET_2_VALUE";
  var secretsJson = JSON.stringify(secretsObj);

  // Act
  await verify_secrets(secretsJson);

  // Assert
  expect(core.setFailed).not.toHaveBeenCalled();
});


test('missing secret', async () => {
  // Arrange
  var secretsObj = new Object();
  secretsObj.SECRET_1 = "SECRET_1_VALUE";
  var secretsJson = JSON.stringify(secretsObj);

  // Act
  await verify_secrets(secretsJson);

  // Assert
  expect(core.setFailed).toHaveBeenCalled();
  expect(core.error).toHaveBeenCalledWith("SECRET_2");
});
