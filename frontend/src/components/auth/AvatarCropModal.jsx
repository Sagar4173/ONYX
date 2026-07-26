import Cropper from "react-easy-crop";
import {
  PhotoIcon,
  XMarkIcon,
  CameraIcon,
  ArrowsPointingOutIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";
import { CheckIcon } from "@heroicons/react/24/solid";

export const AvatarCropModal = ({
  showAvatarModal,
  avatarSource,
  crop,
  zoom,
  croppedAreaPixels,
  savingAvatar,
  avatarPreview,
  user,
  fileInputRef,
  handleCancelAvatarEdit,
  handleSaveAvatar,
  handleRemoveAvatar,
  onCropComplete,
  setCrop,
  setZoom,
  handleAvatarSelect,
}) => {
  if (!showAvatarModal) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-gray-900 border border-gray-700/50 rounded-3xl shadow-2xl w-full max-w-xl overflow-hidden animate-scale-in">
        <div className="px-6 py-4 border-b border-gray-700/50 bg-gradient-to-r from-indigo-500/10 to-purple-500/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-xl">
                <PhotoIcon className="h-5 w-5 text-indigo-400" />
              </div>
              <h3 className="text-lg font-bold text-white">Edit Avatar</h3>
            </div>
            <button
              onClick={handleCancelAvatarEdit}
              aria-label="Cancel avatar edit"
              className="p-2 hover:bg-gray-800/50 rounded-xl transition-all duration-300"
            >
              <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-white" />
            </button>
          </div>
        </div>

        <div className="relative h-80 bg-gray-950 flex items-center justify-center">
          {avatarSource ? (
            <Cropper
              image={avatarSource}
              crop={crop}
              zoom={zoom}
              minZoom={1}
              maxZoom={3}
              aspect={1}
              cropShape="round"
              showGrid={false}
              objectFit="vertical-cover"
              restrictPosition={true}
              onCropChange={setCrop}
              onZoomChange={setZoom}
              onCropComplete={onCropComplete}
              style={{ containerStyle: { backgroundColor: "#030712" } }}
            />
          ) : (
            <div className="flex flex-col items-center gap-5 text-center p-6">
              <div className="w-48 h-48 rounded-full bg-gradient-to-br from-gray-800 to-gray-700 flex items-center justify-center border-4 border-gray-600/50 overflow-hidden shadow-2xl shadow-black/50 ring-4 ring-indigo-500/20">
                {avatarPreview || user?.avatar_url ? (
                  <img
                    src={avatarPreview || user?.avatar_url}
                    alt="Current avatar"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <PhotoIcon className="h-16 w-16 text-gray-500" />
                )}
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-2 px-5 py-3 bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/40 text-indigo-300 hover:text-indigo-200 rounded-xl transition-all duration-300"
              >
                <CameraIcon className="h-5 w-5" />
                <span className="text-sm font-medium">Upload New Photo</span>
              </button>
            </div>
          )}
        </div>

        {avatarSource && (
          <div className="px-6 py-4 bg-gray-800/30 border-t border-gray-700/30">
            <div className="flex items-center gap-4">
              <ArrowsPointingOutIcon className="h-5 w-5 text-gray-400" />
              <input
                type="range"
                min={1}
                max={3}
                step={0.05}
                value={zoom}
                onChange={(e) => setZoom(Number(e.target.value))}
                className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
              <span className="text-gray-400 text-sm font-mono w-12 text-right">
                {Math.round(zoom * 100)}%
              </span>
            </div>
          </div>
        )}

        <div className="px-6 py-4 border-t border-gray-700/50 bg-gray-800/20">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              {(avatarPreview || user?.avatar_url) && (
                <button
                  onClick={handleRemoveAvatar}
                  disabled={savingAvatar}
                  className="flex items-center gap-2 px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 rounded-xl transition-all duration-300 disabled:opacity-50"
                >
                  <TrashIcon className="h-4 w-4" />
                  <span className="text-sm font-medium">Remove</span>
                </button>
              )}
              {avatarSource && (
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-2 px-4 py-2.5 bg-gray-700/50 hover:bg-gray-600/50 border border-gray-600/50 text-gray-300 hover:text-white rounded-xl transition-all duration-300"
                >
                  <CameraIcon className="h-4 w-4" />
                  <span className="text-sm font-medium">Change</span>
                </button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleCancelAvatarEdit}
                disabled={savingAvatar}
                className="px-5 py-2.5 bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700/50 text-gray-300 hover:text-white rounded-xl transition-all duration-300 text-sm font-medium disabled:opacity-50"
              >
                Cancel
              </button>
              {avatarSource && (
                <button
                  onClick={handleSaveAvatar}
                  disabled={savingAvatar || !croppedAreaPixels}
                  className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white rounded-xl transition-all duration-300 text-sm font-medium shadow-lg shadow-indigo-500/30 disabled:opacity-50"
                >
                  {savingAvatar ? (
                    <>
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>{" "}
                      Saving...
                    </>
                  ) : (
                    <>
                      <CheckIcon className="h-4 w-4" /> Save Avatar
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
